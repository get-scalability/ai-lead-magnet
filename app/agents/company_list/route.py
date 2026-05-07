"""SSE endpoint for the Company List agent."""

from collections.abc import AsyncGenerator
import csv
from datetime import UTC, date, datetime
import io
import json
from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse
import structlog

from app.agents.company_list import agent
from app.core.database import get_db
from app.gate.models import LeadMagnetResult
from app.gate.service import check_rate_limit, increment_run, push_to_crm


logger = structlog.get_logger()

router = APIRouter(prefix="/agents/company-list", tags=["company-list"])

TOOL_SLUG = "company_list"


def _next_reset_date() -> str:
    today = date.today()
    first_next = (
        date(today.year + 1, 1, 1) if today.month == 12 else date(today.year, today.month + 1, 1)
    )
    return first_next.strftime("%B %d")


class RunRequest(BaseModel):
    email: EmailStr
    first_name: str | None = None
    domain: str
    icp_prompt: str


@router.post("/stream")
async def stream(
    req: RunRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> EventSourceResponse:
    allowed, _ = await check_rate_limit(db, req.email, TOOL_SLUG)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"message": "Monthly limit reached.", "reset_on": _next_reset_date()},
        )

    # Increment before streaming — prevents double-spend on concurrent requests
    # and survives client disconnects mid-stream.
    await increment_run(db, req.email, TOOL_SLUG)

    async def generate() -> AsyncGenerator[dict[str, str]]:
        result_data: dict | None = None

        async for event in agent.run(req.domain, req.icp_prompt):
            yield event
            if event["event"] == "result":
                result_data = json.loads(event["data"])

        if result_data:
            result_row = LeadMagnetResult(
                tool_slug=TOOL_SLUG,
                input_data={"domain": req.domain, "icp_prompt": req.icp_prompt},
                output_data=result_data,
            )
            db.add(result_row)
            await db.commit()
            await db.refresh(result_row)

            yield {
                "event": "done",
                "data": json.dumps({"public_id": str(result_row.public_id)}),
            }

            await push_to_crm(
                {
                    "email": req.email,
                    "first_name": req.first_name,
                    "tool_used": TOOL_SLUG,
                    "tool_input_summary": f"domain: {req.domain}",
                    "icp_prompt": req.icp_prompt,
                    "company_domain": req.domain,
                    "results_count": result_data.get("total_found", 0),
                    "created_at": datetime.now(UTC).isoformat(),
                }
            )

    return EventSourceResponse(generate())


@router.get("/result/{public_id}")
async def get_result(public_id: str, db: Annotated[AsyncSession, Depends(get_db)]) -> dict:
    try:
        uid = uuid.UUID(public_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid public_id") from None

    row = await db.scalar(
        select(LeadMagnetResult).where(
            LeadMagnetResult.public_id == uid,
            LeadMagnetResult.tool_slug == TOOL_SLUG,
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    return {
        "public_id": str(row.public_id),
        "input": row.input_data,
        "output": row.output_data,
        "created_at": row.created_at.isoformat(),
    }


_CSV_COLUMNS = ["name", "domain", "linkedin_url", "industry", "size", "country", "icp_score"]


@router.get("/result/{public_id}/csv")
async def get_result_csv(
    public_id: str, db: Annotated[AsyncSession, Depends(get_db)]
) -> StreamingResponse:
    try:
        uid = uuid.UUID(public_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid public_id") from None

    row = await db.scalar(
        select(LeadMagnetResult).where(
            LeadMagnetResult.public_id == uid,
            LeadMagnetResult.tool_slug == TOOL_SLUG,
        )
    )
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")

    companies: list[dict] = row.output_data.get("companies", [])

    buf = io.StringIO()
    writer = csv.DictWriter(
        buf, fieldnames=_CSV_COLUMNS, extrasaction="ignore", lineterminator="\n"
    )
    writer.writeheader()
    writer.writerows(companies)

    filename = f"company-list-{public_id[:8]}.csv"
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
