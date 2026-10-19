import logging
from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import Batch, ClaimChecked, Tenant, User
from api.db.session import get_engine
from api.security import Principal, Role
from api.services.checks import check_and_record
from ingest.csv_import import ParsedBatch
from reasoner.kb import load_kb

logger = logging.getLogger("hakiki.batch")


def create_batch(db: Session, principal: Principal, filename: str, parsed: ParsedBatch) -> Batch:
    batch = Batch(
        tenant_id=principal.tenant_id,
        user_id=principal.user_id,
        filename=filename,
        status="queued",
        total=parsed.total,
        processed=0,
        claims=parsed.claims,
        errors=parsed.errors,
    )
    db.add(batch)
    db.commit()
    return batch


def summarise(db: Session, batch: Batch) -> dict:
    rows = db.execute(
        select(
            ClaimChecked.verdict, ClaimChecked.revenue_at_risk_kes, ClaimChecked.failing_rules
        ).where(ClaimChecked.batch_id == batch.id)
    ).all()
    verdicts = Counter(row.verdict for row in rows)
    rules = Counter(rule for row in rows for rule in row.failing_rules)
    kb = load_kb()
    return {
        "claims": len(rows),
        "pass": verdicts["PASS"],
        "at_risk": verdicts["AT_RISK"],
        "will_fail": verdicts["WILL_FAIL"],
        "rows_rejected": len(batch.errors),
        "revenue_at_risk_kes": float(sum(row.revenue_at_risk_kes for row in rows)),
        "top_failing_rules": [
            {"rule": rule, "name": kb.rule(rule)["name"], "count": count}
            for rule, count in sorted(rules.items(), key=lambda item: (-item[1], item[0]))
        ],
    }


def process_batch(batch_id: UUID) -> None:
    with Session(get_engine(), expire_on_commit=False) as db:
        batch = db.get(Batch, batch_id)
        user = db.get(User, batch.user_id)
        tenant = db.get(Tenant, batch.tenant_id)
        principal = Principal(user.id, tenant.id, user.name, tenant.name, Role(user.role))
        batch.status = "processing"
        db.commit()
        try:
            for item in list(batch.claims):
                check_and_record(db, principal, item["claim"], batch.id, item["row"])
                batch.processed += 1
                db.commit()
            batch.summary = summarise(db, batch)
            batch.status = "done"
        except Exception as exc:
            db.rollback()
            logger.error("batch %s failed: %s", batch_id, type(exc).__name__)
            batch = db.get(Batch, batch_id)
            batch.status = "failed"
        batch.claims = []
        batch.finished_at = datetime.now(UTC)
        db.commit()
