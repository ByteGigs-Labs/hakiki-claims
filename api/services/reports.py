from collections import Counter
from datetime import UTC, datetime, timedelta
from itertools import groupby
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import ClaimChecked
from reasoner.kb import load_kb

KENYA = ZoneInfo("Africa/Nairobi")


def _local_date(moment: datetime):
    return moment.astimezone(KENYA).date()


def overview(db: Session, tenant_id: UUID, days: int, now: datetime | None = None) -> dict:
    now = now or datetime.now(UTC)
    since = now - timedelta(days=days)
    rows = db.scalars(
        select(ClaimChecked)
        .where(ClaimChecked.tenant_id == tenant_id, ClaimChecked.checked_at >= since)
        .order_by(ClaimChecked.claim_ref, ClaimChecked.checked_at, ClaimChecked.id)
    ).all()

    verdicts: Counter[str] = Counter()
    rules: Counter[str] = Counter()
    at_risk_total = protected_total = 0.0
    protected_claims = 0
    for _, group in groupby(rows, key=lambda row: row.claim_ref):
        history = list(group)
        first, latest = history[0], history[-1]
        verdicts[latest.verdict] += 1
        if latest.verdict != "PASS":
            at_risk_total += float(latest.revenue_at_risk_kes)
            rules.update(latest.failing_rules)
        elif first.verdict != "PASS":
            protected_total += float(first.revenue_at_risk_kes)
            protected_claims += 1

    kb = load_kb()
    start = _local_date(since)
    end = _local_date(now)
    activity = {start + timedelta(days=offset): [0, 0] for offset in range((end - start).days + 1)}
    for row in rows:
        day = activity.get(_local_date(row.checked_at))
        if day is not None:
            day[0] += 1
            day[1] += row.verdict != "PASS"

    return {
        "days": days,
        "since": since.isoformat(),
        "checks": len(rows),
        "claims": sum(verdicts.values()),
        "passing": verdicts["PASS"],
        "at_risk": verdicts["AT_RISK"],
        "will_fail": verdicts["WILL_FAIL"],
        "revenue_at_risk_kes": at_risk_total,
        "revenue_protected_kes": protected_total,
        "claims_protected": protected_claims,
        "top_failing_rules": [
            {"rule": rule, "name": kb.rule(rule)["name"], "count": count}
            for rule, count in sorted(rules.items(), key=lambda item: (-item[1], int(item[0][1:])))
        ],
        "daily": [
            {"date": day.isoformat(), "checks": checks, "flagged": flagged}
            for day, (checks, flagged) in activity.items()
        ],
    }
