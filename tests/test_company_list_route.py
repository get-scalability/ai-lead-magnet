import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.gate.models import LeadMagnetResult, LeadMagnetRun
from app.gate.service import MONTHLY_LIMIT


_MOCK_HITS = [
    {"company_key": "linkedin_id:111", "score": 0.92},
    {"company_key": "linkedin_id:222", "score": 0.75},
]

_MOCK_ENRICHMENT = {
    "linkedin_id:111": {
        "company_key": "linkedin_id:111",
        "name": "Acme Corp",
        "domain": "acme.com",
        "country": "FR",
        "employees_count": 150,
        "industry": "Software Development",
        "linkedin_url": "https://www.linkedin.com/company/acme",
    },
    "linkedin_id:222": {
        "company_key": "linkedin_id:222",
        "name": "Beta Inc",
        "domain": "beta.com",
        "country": "FR",
        "employees_count": 80,
        "industry": "Software Development",
        "linkedin_url": None,
    },
}

_REQ = {
    "email": "test@example.com",
    "domain": "test.com",
    "icp_prompt": "B2B SaaS companies in France, 50-200 employees",
}


def _mock_icp_response(semantic_query: str = "B2B SaaS companies") -> MagicMock:
    block = MagicMock()
    block.type = "tool_use"
    block.name = "set_icp_params"
    block.input = {"semantic_query": semantic_query}
    msg = MagicMock()
    msg.content = [block]
    return msg


def _parse_sse(text: str) -> list[dict]:
    events: list[dict] = []
    event_type = ""
    for line in text.splitlines():
        if line.startswith("event: "):
            event_type = line[7:].strip()
        elif line.startswith("data: "):
            try:
                events.append({"event": event_type, "data": json.loads(line[6:].strip())})
            except json.JSONDecodeError:
                pass
            event_type = ""
    return events


@pytest.fixture
def mock_agent(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.agents.company_list.agent.scrape_domain",
        AsyncMock(return_value="B2B sales intelligence platform"),
    )
    monkeypatch.setattr(
        "app.agents.company_list.agent._extract_icp_params",
        AsyncMock(return_value={"semantic_query": "B2B SaaS companies"}),
    )
    monkeypatch.setattr(
        "app.agents.company_list.agent.pinecone_search",
        AsyncMock(return_value=_MOCK_HITS),
    )
    monkeypatch.setattr(
        "app.agents.company_list.agent._fetch_companies_by_keys",
        AsyncMock(return_value=_MOCK_ENRICHMENT),
    )
    monkeypatch.setattr(
        "app.agents.company_list.route.push_to_crm",
        AsyncMock(),
    )


class TestStream:
    async def test_successful_run_returns_result_and_done(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        response = await client.post("/agents/company-list/stream", json=_REQ)
        assert response.status_code == 200

        events = _parse_sse(response.text)
        types = [e["event"] for e in events]
        assert "result" in types
        assert "done" in types

    async def test_result_event_has_companies(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        response = await client.post("/agents/company-list/stream", json=_REQ)
        events = _parse_sse(response.text)
        result = next(e["data"] for e in events if e["event"] == "result")

        assert len(result["companies"]) == 2
        assert result["total_found"] == 2
        assert result["companies"][0]["name"] == "Acme Corp"

    async def test_done_event_has_public_id(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        response = await client.post("/agents/company-list/stream", json=_REQ)
        events = _parse_sse(response.text)
        done = next(e["data"] for e in events if e["event"] == "done")
        assert done["public_id"]

    async def test_run_is_persisted_in_db(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        await client.post("/agents/company-list/stream", json=_REQ)
        row = await db.scalar(select(LeadMagnetRun))
        assert row is not None
        assert row.run_count == 1

    async def test_result_is_persisted_in_db(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        await client.post("/agents/company-list/stream", json=_REQ)
        row = await db.scalar(select(LeadMagnetResult))
        assert row is not None
        assert row.tool_slug == "company_list"
        assert len(row.output_data["companies"]) == 2

    async def test_rate_limit_blocks_on_fourth_run(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        for _ in range(MONTHLY_LIMIT):
            r = await client.post("/agents/company-list/stream", json=_REQ)
            assert r.status_code == 200

        r = await client.post("/agents/company-list/stream", json=_REQ)
        assert r.status_code == 429

    async def test_missing_email_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/agents/company-list/stream",
            json={"domain": "test.com", "icp_prompt": "..."},
        )
        assert response.status_code == 422

    async def test_invalid_email_returns_422(self, client: AsyncClient) -> None:
        response = await client.post(
            "/agents/company-list/stream",
            json={**_REQ, "email": "not-an-email"},
        )
        assert response.status_code == 422


class TestGetResult:
    async def test_returns_stored_result(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        stream_resp = await client.post("/agents/company-list/stream", json=_REQ)
        events = _parse_sse(stream_resp.text)
        public_id = next(e["data"]["public_id"] for e in events if e["event"] == "done")

        response = await client.get(f"/agents/company-list/result/{public_id}")
        assert response.status_code == 200
        body = response.json()
        assert body["public_id"] == public_id
        assert "companies" in body["output"]

    async def test_invalid_uuid_returns_400(self, client: AsyncClient) -> None:
        response = await client.get("/agents/company-list/result/not-a-uuid")
        assert response.status_code == 400

    async def test_unknown_uuid_returns_404(self, client: AsyncClient) -> None:
        response = await client.get(
            "/agents/company-list/result/00000000-0000-0000-0000-000000000000"
        )
        assert response.status_code == 404


class TestGetResultCsv:
    async def test_returns_csv_with_correct_headers(
        self, client: AsyncClient, db: AsyncSession, mock_agent: None
    ) -> None:
        stream_resp = await client.post("/agents/company-list/stream", json=_REQ)
        events = _parse_sse(stream_resp.text)
        public_id = next(e["data"]["public_id"] for e in events if e["event"] == "done")

        response = await client.get(f"/agents/company-list/result/{public_id}/csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]
        lines = response.text.strip().splitlines()
        assert lines[0] == "name,domain,linkedin_url,industry,size,country,icp_score"
        assert len(lines) == 3  # header + 2 companies

    async def test_unknown_uuid_returns_404(self, client: AsyncClient) -> None:
        response = await client.get(
            "/agents/company-list/result/00000000-0000-0000-0000-000000000000/csv"
        )
        assert response.status_code == 404
