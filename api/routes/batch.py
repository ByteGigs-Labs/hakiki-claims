from datetime import datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db.models import Batch, ClaimChecked
from api.db.session import get_db
from api.ratelimit import batch_limit
from api.security import Principal, current_principal
from api.services.batches import create_batch, process_batch
from ingest.csv_import import CsvImportError, parse_csv, safe_filename, template_csv

router = APIRouter(prefix="/v1/claims/batch", tags=["batch"])

CSV_CONTENT_TYPES = {"text/csv", "application/csv", "application/vnd.ms-excel", "text/plain"}
MAX_PAGE_SIZE = 100
Verdict = Literal["PASS", "AT_RISK", "WILL_FAIL"]


class BatchStatus(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    filename: str
    status: str
    total: int
    processed: int
    errors: list[dict]
    summary: dict | None
    created_at: datetime
    finished_at: datetime | None


class BatchRow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    row_number: int | None
    claim_ref: str
    service_code: str
    fund: str
    amount_kes: Decimal
    verdict: Verdict
    revenue_at_risk_kes: Decimal
    failing_rules: list[str]
    trace_hash: str


def _owned_batch(db: Session, principal: Principal, batch_id: UUID) -> Batch:
    batch = db.scalar(
        select(Batch).where(Batch.id == batch_id, Batch.tenant_id == principal.tenant_id)
    )
    if not batch:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Batch not found")
    return batch


@router.get("/template")
def download_template(_: Principal = Depends(current_principal)) -> Response:
    return Response(
        template_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="hakiki-claims-template.csv"'},
    )


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def upload_batch(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    principal: Principal = Depends(batch_limit),
    db: Session = Depends(get_db),
) -> BatchStatus:
    settings = get_settings()
    if file.content_type not in CSV_CONTENT_TYPES or not (file.filename or "").lower().endswith(
        ".csv"
    ):
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Upload a .csv file")
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File is too large")
    try:
        parsed = parse_csv(content, settings.max_batch_rows)
    except CsvImportError as error:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, str(error)) from error
    batch = create_batch(db, principal, safe_filename(file.filename), parsed)
    background.add_task(process_batch, batch.id)
    return BatchStatus.model_validate(batch)


@router.get("")
def recent_batches(
    limit: int = Query(5, ge=1, le=20),
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> list[BatchStatus]:
    batches = db.scalars(
        select(Batch)
        .where(Batch.tenant_id == principal.tenant_id)
        .order_by(Batch.created_at.desc())
        .limit(limit)
    )
    return [BatchStatus.model_validate(batch) for batch in batches]


@router.get("/{batch_id}")
def batch_status(
    batch_id: UUID,
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> BatchStatus:
    return BatchStatus.model_validate(_owned_batch(db, principal, batch_id))


@router.get("/{batch_id}/rows")
def batch_rows(
    batch_id: UUID,
    response: Response,
    verdict: Verdict | None = None,
    start: int = Query(0, alias="_start", ge=0),
    end: int = Query(20, alias="_end", ge=1),
    principal: Principal = Depends(current_principal),
    db: Session = Depends(get_db),
) -> list[BatchRow]:
    batch = _owned_batch(db, principal, batch_id)
    if end <= start or end - start > MAX_PAGE_SIZE:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Invalid page range")
    scope = [ClaimChecked.batch_id == batch.id, ClaimChecked.tenant_id == principal.tenant_id]
    if verdict:
        scope.append(ClaimChecked.verdict == verdict)
    rows = db.scalars(
        select(ClaimChecked)
        .where(*scope)
        .order_by(ClaimChecked.row_number)
        .offset(start)
        .limit(end - start)
    )
    response.headers["X-Total-Count"] = str(
        db.scalar(select(func.count()).select_from(ClaimChecked).where(*scope))
    )
    return [BatchRow.model_validate(row) for row in rows]
