"""Read-only Pinecone client for semantic company search (scala-db index)."""

import asyncio
from typing import Any

from pinecone import Pinecone, SearchQuery
import structlog

from app.core.settings import settings


logger = structlog.get_logger()

_SCALA_DB_INDEX = "scala-db"
_COMPANIES_NAMESPACE = "companies"

_client: Pinecone | None = None


def _get_client() -> Pinecone:
    global _client  # noqa: PLW0603
    if _client is None:
        _client = Pinecone(api_key=settings.PINECONE_RO_API_KEY.get_secret_value())
    return _client


async def search_companies(
    query_text: str,
    top_k: int = 200,
    metadata_filter: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Semantic search in the companies namespace of scala-db.

    Returns list of dicts with company metadata and score.
    """
    index = _get_client().Index(_SCALA_DB_INDEX)

    response = await asyncio.to_thread(
        index.search_records,
        _COMPANIES_NAMESPACE,
        SearchQuery(
            inputs={"text": query_text},
            top_k=top_k,
            filter=metadata_filter,
        ),
    )

    results: list[dict[str, Any]] = []
    for hit in response.result.hits:
        fields = hit.get("fields", {}) if isinstance(hit, dict) else getattr(hit, "fields", {})
        hit_id = hit.get("_id", "") if isinstance(hit, dict) else getattr(hit, "_id", "")
        score = hit.get("_score", 0.0) if isinstance(hit, dict) else getattr(hit, "_score", 0.0)
        results.append(
            {
                "id": hit_id,
                "score": score,
                "text": fields.get("text", ""),
                "city": fields.get("city"),
                "domain": fields.get("domain"),
                "company_key": fields.get("company_key"),
                "country": fields.get("country"),
                "employees_count": fields.get("employees_count"),
                "funding_stage": fields.get("funding_stage"),
                "headcount_increasing": fields.get("headcount_increasing"),
                "hiring": fields.get("hiring"),
                "industry": fields.get("industry"),
                "name": fields.get("name"),
            }
        )

    logger.info("pinecone_companies_searched", query_length=len(query_text), results=len(results))
    return results
