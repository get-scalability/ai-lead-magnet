"""Direct REST client for the Scala App API (https://api.getscalability.io/)."""

from typing import Any

import httpx
import structlog

from app.core.settings import settings


logger = structlog.get_logger()

_COMPANY_PROJECTION = {
    "company_name": True,
    "domain": True,
    "company_linkedin_url": True,
    "linkedin_industry": True,
    "gpt_industry": True,
    "gpt_description": True,
    "employees_count": True,
    "employees_range": True,
    "country_code": True,
}


def _client() -> httpx.AsyncClient:
    base = settings.SCALA_APP_API_URL.rstrip("/")
    return httpx.AsyncClient(
        base_url=base,
        headers={
            "X-API-Key": settings.SCALA_APP_API_KEY.get_secret_value(),
            "X-Tenant-ID": settings.SCALA_TENANT_ID,
        },
        timeout=30.0,
    )


def _normalise_filters(filters: dict[str, Any]) -> dict[str, Any]:
    """Uppercase ISO country codes and normalise any casing issues."""
    out = dict(filters)
    if codes := out.get("company_country_codes"):
        out["company_country_codes"] = [c.upper() for c in codes]
    return out


async def search_companies(
    search_filters: dict[str, Any],
    sample_size: int = 60,
) -> list[dict[str, Any]]:
    """POST /api/v1/audience_builder_v2/company/search → flat company dicts."""
    body = {
        "sample_size": sample_size,
        "search_filters": _normalise_filters(search_filters),
        "table_mode": "all",
        "static_projection": _COMPANY_PROJECTION,
    }
    logger.info("scala_search", filters=search_filters, sample_size=sample_size)
    async with _client() as client:
        resp = await client.post("/api/v1/audience_builder_v2/company/search", json=body)
        resp.raise_for_status()

    raw: list[dict] = resp.json()
    return [item["company"] for item in raw if item.get("company")]
