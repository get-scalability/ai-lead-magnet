"""Company List agent — semantic search via Pinecone + Snowflake enrichment.

Search pipeline:
  1. Scrape user's domain → understand what the SELLER offers (context only)
  2. Claude Haiku extracts ICP params: semantic_query (TARGET companies) + optional filters
  3. Pinecone semantic search on scala-db/companies namespace
  4. Filter results below minimum relevance score
  5. Snowflake enrichment by company_key (name, domain, LinkedIn URL, etc.)
  6. Return top 50 sorted by Pinecone score

CRITICAL: The user's domain is seller context only. The semantic_query MUST describe
TARGET companies (buyers), never the seller's own company.
"""

from collections.abc import AsyncGenerator
import json
from typing import Any

import anthropic
import structlog

from app.core.http import scrape_domain
from app.core.pinecone_client import search_companies as pinecone_search
from app.core.settings import settings
from app.core.snowflake import get_pool


logger = structlog.get_logger()

_anthropic = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())

_MIN_SEMANTIC_SCORE = 0.35
_TOP_N = 50

_ICP_PARAMS_TOOL: dict[str, Any] = {
    "name": "set_icp_params",
    "description": (
        "Extract search parameters to find TARGET companies matching the seller's ICP. "
        "The semantic_query MUST describe the TARGET companies (buyers), never the seller."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "semantic_query": {
                "type": "string",
                "description": (
                    "MUST be written in English. "
                    "A concise profile (2-3 sentences) of the TARGET companies — what they "
                    "are, what industry they operate in, their typical size and business model. "
                    "Focus on what these companies DO and what they ARE, not what they need. "
                    "Example: 'Mid-sized B2B SaaS company providing project management software "
                    "to enterprises. Typical size 50-200 employees, primarily in Europe.' "
                    "NEVER describe the seller's own company here."
                ),
            },
            "country": {
                "type": "string",
                "description": "ISO-2 country code (e.g. 'FR', 'US'). Only if explicitly set.",
            },
            "min_employees": {
                "type": "integer",
                "description": "Minimum employee count. Only if explicitly specified.",
            },
            "max_employees": {
                "type": "integer",
                "description": "Maximum employee count. Only if explicitly specified.",
            },
            "industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "One or more LinkedIn industry values to filter on (OR logic). "
                    "Only use when the user specifies a clear industry. "
                    "For broad categories like 'SaaS' or 'tech', omit this field and rely "
                    "on the semantic_query instead. "
                    "Valid values (use exactly as written): "
                    "'Software Development', 'IT Services and IT Consulting', "
                    "'Information Technology and Services', "
                    "'Technology, Information and Internet', "
                    "'Business Consulting and Services', 'Financial Services', "
                    "'Marketing Services', 'Advertising Services', "
                    "'Health, Wellness and Fitness', 'Hospitals and Health Care', "
                    "'Manufacturing', 'Industrial Machinery Manufacturing', "
                    "'Staffing and Recruiting', 'E-Learning Providers', "
                    "'Professional Services'."
                ),
            },
            "hiring": {
                "type": "boolean",
                "description": "True to filter to companies actively hiring.",
            },
            "headcount_increasing": {
                "type": "boolean",
                "description": "True to filter to companies with growing headcount.",
            },
        },
        "required": ["semantic_query"],
    },
}


async def _extract_icp_params(domain_context: str, icp_prompt: str) -> dict[str, Any]:
    """Convert ICP prompt + seller context into a semantic query + optional Pinecone filters.

    The prompt explicitly separates SELLER context from TARGET description so Claude
    never confuses the two and never generates a look-alike query for the seller's domain.
    """
    msg = await _anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=[_ICP_PARAMS_TOOL],  # type: ignore[arg-type]
        tool_choice={"type": "tool", "name": "set_icp_params"},
        messages=[
            {
                "role": "user",
                "content": (
                    "SELLER CONTEXT (understand what they sell, not what they're looking for):\n"
                    f"{domain_context or 'Not available'}\n\n"
                    "TARGET ICP (provided by the seller — these are the companies to find, "
                    "not the seller):\n"
                    f"{icp_prompt}\n\n"
                    "Extract search parameters to find TARGET companies.\n"
                    "The semantic_query MUST be written in English and describe the TARGET "
                    "companies (what they are and what they do), never the seller. "
                    "Use the seller context only to better understand their offer and identify "
                    "who would be a good buyer."
                ),
            }
        ],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "set_icp_params":
            return block.input
    return {"semantic_query": icp_prompt}


def _build_pinecone_filter(  # noqa: PLR0913
    *,
    country: str | None = None,
    industries: list[str] | None = None,
    min_employees: int | None = None,
    max_employees: int | None = None,
    hiring: bool | None = None,
    headcount_increasing: bool | None = None,
) -> dict[str, Any] | None:
    f: dict[str, Any] = {}
    if country:
        f["country"] = country
    if industries:
        f["industry"] = {"$in": industries}
    if min_employees is not None or max_employees is not None:
        emp: dict[str, int] = {}
        if min_employees is not None:
            emp["$gte"] = min_employees
        if max_employees is not None:
            emp["$lte"] = max_employees
        f["employees_count"] = emp
    if hiring is not None:
        f["hiring"] = hiring
    if headcount_increasing is not None:
        f["headcount_increasing"] = headcount_increasing
    return f or None


async def _fetch_companies_by_keys(keys: list[str]) -> dict[str, dict]:
    """Fetch enriched company data from Snowflake by company_key list."""
    if not keys:
        return {}

    placeholders = ", ".join(f"%(key_{i})s" for i in range(len(keys)))
    params: dict[str, Any] = {f"key_{i}": k for i, k in enumerate(keys)}

    query = f"""  # noqa: S608
        SELECT
            COMPANY_KEY,
            COMPANY_NAME,
            COMPANY_DOMAIN,
            COMPANY_COUNTRY_CODE,
            COMPANY_EMPLOYEES_COUNT,
            COMPANY_LINKEDIN_INDUSTRY,
            COMPANY_LINKEDIN_UNIVERSAL_NAME,
            COMPANY_LINKEDIN_ID,
            HIRING,
            HEADCOUNT_IS_INCREASING
        FROM dbt_db.models_final.final_companies_flatten
        WHERE COMPANY_KEY IN ({placeholders})
    """

    pool = get_pool()
    rows = await pool.execute(query, params)

    result: dict[str, dict] = {}
    for row in rows:
        key = row.get("COMPANY_KEY")
        if not key:
            continue
        universal_name = row.get("COMPANY_LINKEDIN_UNIVERSAL_NAME")
        linkedin_id = row.get("COMPANY_LINKEDIN_ID")
        linkedin_url: str | None = None
        if universal_name:
            linkedin_url = f"https://www.linkedin.com/company/{universal_name}"
        elif linkedin_id:
            linkedin_url = f"https://www.linkedin.com/company/{linkedin_id}"
        result[key] = {
            "company_key": key,
            "name": row.get("COMPANY_NAME") or "",
            "domain": row.get("COMPANY_DOMAIN") or "",
            "country": row.get("COMPANY_COUNTRY_CODE") or "",
            "employees_count": row.get("COMPANY_EMPLOYEES_COUNT"),
            "industry": row.get("COMPANY_LINKEDIN_INDUSTRY") or "",
            "linkedin_url": linkedin_url,
        }
    return result


def _score_to_pct(score: float) -> int:
    """Map Pinecone cosine score [_MIN_SEMANTIC_SCORE, 1.0] → [0, 100]."""
    clamped = max(_MIN_SEMANTIC_SCORE, min(1.0, score))
    return round((clamped - _MIN_SEMANTIC_SCORE) / (1.0 - _MIN_SEMANTIC_SCORE) * 100)


def _format_company(c: dict[str, Any]) -> dict[str, Any]:
    emp = c.get("employees_count")
    return {
        "company_key": c.get("company_key", ""),
        "name": c.get("name") or "",
        "domain": c.get("domain") or "",
        "linkedin_url": c.get("linkedin_url"),
        "industry": c.get("industry") or "",
        "size": str(emp) if emp is not None else "",
        "country": c.get("country") or "",
        "icp_score": c.get("icp_score", 0),
    }


async def run(
    user_domain: str,
    icp_prompt: str,
) -> AsyncGenerator[dict[str, str]]:
    """Run the Company List agent. Yields SSE event dicts {event, data}.

    The user's domain is used ONLY to understand what the seller offers.
    It is never used to find look-alike companies.
    """

    def _status(message: str, detail: str = "") -> dict[str, str]:
        return {"event": "status", "data": json.dumps({"message": message, "detail": detail})}

    yield _status(f"🔍 Analyzing {user_domain}...")
    domain_context = await scrape_domain(user_domain)

    yield _status("🔍 Building search parameters from your ICP criteria...")
    params = await _extract_icp_params(domain_context, icp_prompt)
    semantic_query = params.get("semantic_query") or icp_prompt
    logger.info("company_list_icp_params", params=params)

    metadata_filter = _build_pinecone_filter(
        country=params.get("country"),
        industries=params.get("industries"),
        min_employees=params.get("min_employees"),
        max_employees=params.get("max_employees"),
        hiring=params.get("hiring"),
        headcount_increasing=params.get("headcount_increasing"),
    )

    filter_desc = ""
    if params.get("country"):
        filter_desc += f" · {params['country']}"
    if params.get("min_employees") or params.get("max_employees"):
        lo = params.get("min_employees", 0)
        hi = params.get("max_employees")
        filter_desc += f" · {lo}-{hi or '∞'} employees"

    yield _status(
        "🔍 Searching our database for matching companies...",
        f"Semantic search{filter_desc}",
    )

    try:
        pinecone_hits = await pinecone_search(
            query_text=semantic_query,
            top_k=200,
            metadata_filter=metadata_filter,
        )
    except Exception:
        logger.exception("pinecone_search_failed")
        yield {
            "event": "error",
            "data": json.dumps({"message": "Database search failed. Please try again."}),
        }
        return

    pinecone_hits = [h for h in pinecone_hits if h.get("score", 0) >= _MIN_SEMANTIC_SCORE]

    if not pinecone_hits:
        yield {
            "event": "error",
            "data": json.dumps(
                {
                    "message": "No companies found matching your criteria.",
                    "hint": "Try broadening your description or changing the target region.",
                }
            ),
        }
        return

    yield _status(
        "🔍 Enriching results with detailed company data...",
        f"Found {len(pinecone_hits)} semantic matches",
    )

    keys = [h["company_key"] for h in pinecone_hits if h.get("company_key")]
    enrichment: dict[str, dict] = {}
    try:
        enrichment = await _fetch_companies_by_keys(keys)
    except Exception:
        logger.exception("snowflake_enrichment_failed")

    companies: list[dict] = []
    for hit in pinecone_hits:
        key = hit.get("company_key") or ""
        score = hit.get("score", 0.0)
        if key and key in enrichment:
            c = dict(enrichment[key])
            c["icp_score"] = _score_to_pct(score)
            c["pinecone_score"] = score
        else:
            c = {
                "company_key": key,
                "name": hit.get("name") or "",
                "domain": hit.get("domain") or "",
                "country": hit.get("country") or "",
                "employees_count": hit.get("employees_count"),
                "industry": hit.get("industry") or "",
                "linkedin_url": None,
                "icp_score": _score_to_pct(score),
                "pinecone_score": score,
            }
        companies.append(c)

    companies.sort(key=lambda x: x.get("pinecone_score", 0), reverse=True)
    top_results = companies[:_TOP_N]

    yield _status(f"⚡ Ranking {len(top_results)} accounts by ICP fit...")

    formatted = [_format_company(c) for c in top_results]

    broaden: list[dict[str, str]] = []
    if len(top_results) < _TOP_N:
        broaden = _build_broaden_suggestions(params)

    yield {
        "event": "result",
        "data": json.dumps(
            {
                "companies": formatted,
                "total_found": len(top_results),
                "broaden_suggestions": broaden,
            }
        ),
    }


def _build_broaden_suggestions(params: dict[str, Any]) -> list[dict[str, str]]:
    suggestions = []
    if params.get("min_employees") or params.get("max_employees"):
        suggestions.append({"label": "Remove size filter →", "hint": "~+18 more companies"})
    if params.get("country"):
        suggestions.append({"label": "Expand to more countries →", "hint": "~+25 more companies"})
    if params.get("industries"):
        suggestions.append({"label": "Broaden industry criteria →", "hint": "~+12 more companies"})
    return suggestions[:3]
