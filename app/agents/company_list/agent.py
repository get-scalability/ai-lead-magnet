"""Company List agent — ICP filter extraction + Scala search + Claude scoring."""

import json
from collections.abc import AsyncGenerator
from typing import Any

import anthropic
import structlog

from app.core.http import scrape_domain
from app.core.scala_api import search_companies
from app.core.settings import settings


logger = structlog.get_logger()

_anthropic = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY.get_secret_value())

_FILTER_TOOL: dict[str, Any] = {
    "name": "set_search_filters",
    "description": (
        "Set structured company search filters based on the user's ICP description. "
        "Use ISO 3166-1 alpha-2 codes for countries (e.g. 'fr', 'us', 'de'). "
        "For company_linkedin_industries use exact LinkedIn industry names. "
        "Leave a filter absent (do not include the key) if it should not be applied."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "company_linkedin_industries": {
                "type": "array",
                "items": {"type": "string"},
                "description": "LinkedIn industry names, e.g. ['computer software', 'information technology and services']",
            },
            "company_gpt_industries": {
                "type": "array",
                "items": {
                    "type": "string",
                    "enum": [
                        "Cybersecurity",
                        "Energy",
                        "Fintech",
                        "Medical equipment",
                        "Miscellaneous",
                        "Salestech & Martech",
                        "Sport",
                        "Technology",
                        "Travel",
                    ],
                },
                "description": (
                    "GPT-classified industry from a fixed list. "
                    "'Technology' covers SaaS/software/IT. "
                    "'Salestech & Martech' covers sales/marketing tools. "
                    "Leave unset to search across all industries."
                ),
            },
            "company_country_codes": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ISO-2 country codes, e.g. ['fr', 'be', 'ch']",
            },
            "company_employee_count_min": {
                "type": "integer",
                "description": "Minimum employee count",
            },
            "company_employee_count_max": {
                "type": "integer",
                "description": "Maximum employee count",
            },
            "company_linkedin_keywords": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Keywords to match against company LinkedIn description/specialties",
            },
            "company_is_hiring": {
                "type": "boolean",
                "description": "Filter to companies that are actively hiring",
            },
            "company_headcount_increased": {
                "type": "boolean",
                "description": "Filter to companies whose headcount increased recently",
            },
        },
        "required": [],
    },
}

_SCORE_TOOL: dict[str, Any] = {
    "name": "rank_companies",
    "description": "Rank companies by ICP fit. Assign a score 0–100 per company (100 = perfect ICP match).",
    "input_schema": {
        "type": "object",
        "properties": {
            "rankings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "company_key": {"type": "string"},
                        "icp_score": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 100,
                        },
                    },
                    "required": ["company_key", "icp_score"],
                },
            }
        },
        "required": ["rankings"],
    },
}


async def _extract_filters(domain_context: str, icp_prompt: str) -> dict[str, Any]:
    """Ask Claude to convert ICP prompt + domain context into Scala search filters."""
    msg = await _anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        tools=[_FILTER_TOOL],
        tool_choice={"type": "tool", "name": "set_search_filters"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"The user's company context (from their website):\n{domain_context or 'Not available'}\n\n"
                    f"Their target ICP description:\n{icp_prompt}\n\n"
                    "Extract company search filters. Be precise — overly broad filters return noise."
                ),
            }
        ],
    )
    for block in msg.content:
        if block.type == "tool_use" and block.name == "set_search_filters":
            return block.input  # type: ignore[return-value]
    return {}


async def _score_companies(
    companies: list[dict[str, Any]],
    icp_prompt: str,
    domain_context: str,
) -> list[dict[str, Any]]:
    """Ask Claude to score each company 0–100 for ICP fit, then sort descending."""
    company_lines = []
    for c in companies:
        line = (
            f"{c.get('company_key', '')} | "
            f"{c.get('cleaned_name') or c.get('name', '?')} | "
            f"{c.get('domain', '?')} | "
            f"{c.get('gpt_industry') or c.get('linkedin_industry', '?')} | "
            f"{c.get('employees_range') or c.get('employees_count', '?')} | "
            f"{c.get('country_code', '?')}"
        )
        if c.get("gpt_description"):
            line += f" | {c['gpt_description'][:120]}"
        company_lines.append(line)

    companies_text = "\n".join(company_lines)

    msg = await _anthropic.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=4096,
        tools=[_SCORE_TOOL],
        tool_choice={"type": "tool", "name": "rank_companies"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Seller context: {domain_context[:500] or 'Not available'}\n\n"
                    f"Target ICP: {icp_prompt}\n\n"
                    "Rate each company below for ICP fit (0–100). "
                    "Format: company_key | name | domain | industry | size | country [| description]\n\n"
                    f"{companies_text}"
                ),
            }
        ],
    )

    score_map: dict[str, int] = {}
    for block in msg.content:
        if block.type == "tool_use" and block.name == "rank_companies":
            for item in block.input.get("rankings", []):
                score_map[item["company_key"]] = item["icp_score"]

    # Attach scores and sort descending
    scored = []
    for c in companies:
        key = c.get("company_key", "")
        c["icp_score"] = score_map.get(key, 50)
        scored.append(c)

    return sorted(scored, key=lambda x: x["icp_score"], reverse=True)


def _format_company(c: dict[str, Any]) -> dict[str, Any]:
    """Normalise a raw Scala company dict into the frontend table row format."""
    name = c.get("cleaned_name") or c.get("name") or ""
    domain = c.get("domain") or ""
    linkedin_url = c.get("linkedin_url") or (
        f"https://www.linkedin.com/company/{c['linkedin_universal_name']}"
        if c.get("linkedin_universal_name")
        else None
    )
    return {
        "company_key": c.get("company_key", ""),
        "name": name,
        "domain": domain,
        "linkedin_url": linkedin_url,
        "industry": c.get("gpt_industry") or c.get("linkedin_industry") or "",
        "size": c.get("employees_range") or (str(c["employees_count"]) if c.get("employees_count") else ""),
        "country": c.get("country_code") or "",
        "icp_score": c.get("icp_score", 50),
    }


async def run(
    user_domain: str,
    icp_prompt: str,
) -> AsyncGenerator[dict[str, str], None]:
    """Run the Company List agent. Yields SSE event dicts {event, data}."""

    def _status(message: str, detail: str = "") -> dict[str, str]:
        return {"event": "status", "data": json.dumps({"message": message, "detail": detail})}

    yield _status(f"🔍 Analyzing {user_domain}...")
    domain_context = await scrape_domain(user_domain)

    yield _status("🔍 Building search filters from your ICP criteria...")
    filters = await _extract_filters(domain_context, icp_prompt)
    logger.info("company_list_filters", filters=filters)

    industry_hint = ""
    if filters.get("company_linkedin_industries"):
        industry_hint = filters["company_linkedin_industries"][0]
    elif filters.get("company_gpt_industries"):
        industry_hint = filters["company_gpt_industries"][0]

    yield _status(
        "🔍 Searching our database for matching companies...",
        f"Applying ICP criteria{': ' + industry_hint if industry_hint else ''}",
    )

    try:
        raw_companies = await search_companies(filters, sample_size=80)
    except Exception:
        logger.exception("scala_search_failed")
        yield {"event": "error", "data": json.dumps({"message": "Database search failed. Please try again."})}
        return

    if not raw_companies:
        yield {
            "event": "error",
            "data": json.dumps({
                "message": "No companies found matching your criteria.",
                "hint": "Try broadening your description or changing the target region.",
            }),
        }
        return

    yield _status(
        "🔍 Scoring + filtering results...",
        f"Found {len(raw_companies)} candidates",
    )
    scored = await _score_companies(raw_companies, icp_prompt, domain_context)

    top_50 = scored[:50]
    yield _status(f"⚡ Ranking {len(top_50)} accounts by ICP fit...")

    companies = [_format_company(c) for c in top_50]

    # Build broaden suggestions if fewer than 50
    broaden: list[dict[str, str]] = []
    if len(top_50) < 50:
        broaden = _build_broaden_suggestions(filters)

    yield {
        "event": "result",
        "data": json.dumps({
            "companies": companies,
            "total_found": len(top_50),
            "broaden_suggestions": broaden,
        }),
    }


def _build_broaden_suggestions(
    filters: dict[str, Any],
) -> list[dict[str, str]]:
    suggestions = []
    if filters.get("company_employee_count_min") or filters.get("company_employee_count_max"):
        suggestions.append({"label": "Remove size filter →", "hint": "~+18 more companies"})
    if filters.get("company_country_codes") and len(filters["company_country_codes"]) <= 2:
        suggestions.append({"label": "Expand to more countries →", "hint": "~+25 more companies"})
    if filters.get("company_linkedin_industries") and len(filters["company_linkedin_industries"]) <= 2:
        suggestions.append({"label": "Broaden industry criteria →", "hint": "~+12 more companies"})
    return suggestions[:3]
