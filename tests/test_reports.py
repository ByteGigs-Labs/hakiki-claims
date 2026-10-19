from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import update

from api.db.models import ClaimChecked
from api.security import Principal, Role
from api.services.checks import record_check
from api.services.reports import overview

NOW = datetime(2026, 10, 19, 9, 0, tzinfo=UTC)


@pytest.fixture
def record(db, make_user, claim, result):
    user = make_user("fin@mercy.test", role=Role.FINANCE_MANAGER)
    actor = Principal(user.id, user.tenant_id, user.name, "Mercy", Role.FINANCE_MANAGER)

    def add(
        claim_ref: str, verdict: str, at: datetime, amount: int = 45000, rules=("R3",), tenant=None
    ):
        passing = verdict == "PASS"
        outcome = {
            **result,
            "claim": claim_ref,
            "verdict": verdict,
            "revenue_at_risk_kes": 0 if passing else amount,
            "trace": [
                {"step": number, "rule": f"{rule}-X", "result": "fail", "fact": "x"}
                for number, rule in enumerate([] if passing else rules, start=1)
            ],
        }
        stored = record_check(
            db, actor, {**claim, "claim_ref": claim_ref, "amount_kes": amount}, outcome
        )
        db.execute(
            update(ClaimChecked)
            .where(
                ClaimChecked.trace_hash == stored["trace_hash"], ClaimChecked.claim_ref == claim_ref
            )
            .values(checked_at=at)
        )
        db.commit()

    return actor, add


def test_empty_tenant_reports_zeros_with_a_full_day_series(db, make_tenant):
    report = overview(db, make_tenant().id, 7, NOW)
    assert (report["checks"], report["claims"], report["revenue_at_risk_kes"]) == (0, 0, 0)
    assert len(report["daily"]) == 8 and all(day["checks"] == 0 for day in report["daily"])


def test_a_claim_fixed_after_failing_counts_as_revenue_protected(db, record):
    actor, add = record
    add("clm-1", "WILL_FAIL", NOW - timedelta(days=3), amount=45000)
    add("clm-1", "PASS", NOW - timedelta(days=3, hours=-1), amount=45000)
    report = overview(db, actor.tenant_id, 30, NOW)
    assert (report["revenue_protected_kes"], report["claims_protected"]) == (45000, 1)
    assert (report["passing"], report["revenue_at_risk_kes"]) == (1, 0)


def test_only_the_latest_check_of_a_claim_counts_as_at_risk(db, record):
    actor, add = record
    add("clm-2", "WILL_FAIL", NOW - timedelta(days=5), amount=10000, rules=("R3", "R6"))
    add("clm-2", "WILL_FAIL", NOW - timedelta(days=4), amount=10000, rules=("R3",))
    report = overview(db, actor.tenant_id, 30, NOW)
    assert (report["claims"], report["will_fail"], report["revenue_at_risk_kes"]) == (1, 1, 10000)
    assert [(rule["rule"], rule["count"]) for rule in report["top_failing_rules"]] == [("R3", 1)]
    assert report["checks"] == 2


def test_clean_claims_are_not_protected_revenue(db, record):
    actor, add = record
    add("clm-3", "PASS", NOW - timedelta(days=2))
    report = overview(db, actor.tenant_id, 30, NOW)
    assert (report["passing"], report["revenue_protected_kes"], report["claims_protected"]) == (
        1,
        0,
        0,
    )


def test_top_rules_are_ranked_by_count_then_rule_number(db, record):
    actor, add = record
    add("a", "WILL_FAIL", NOW - timedelta(days=1), rules=("R6",))
    add("b", "WILL_FAIL", NOW - timedelta(days=1), rules=("R3",))
    add("c", "WILL_FAIL", NOW - timedelta(days=1), rules=("R3", "R10"))
    rules = overview(db, actor.tenant_id, 30, NOW)["top_failing_rules"]
    assert [(rule["rule"], rule["count"]) for rule in rules] == [("R3", 2), ("R6", 1), ("R10", 1)]
    assert rules[0]["name"] == "Pre-authorisation"


def test_checks_outside_the_window_are_ignored(db, record):
    actor, add = record
    add("old", "WILL_FAIL", NOW - timedelta(days=40))
    add("new", "WILL_FAIL", NOW - timedelta(days=2))
    assert overview(db, actor.tenant_id, 30, NOW)["claims"] == 1
    assert overview(db, actor.tenant_id, 60, NOW)["claims"] == 2


def test_daily_buckets_use_the_kenyan_calendar_day(db, record):
    actor, add = record
    add("late", "WILL_FAIL", datetime(2026, 10, 17, 21, 30, tzinfo=UTC))
    daily = {day["date"]: day for day in overview(db, actor.tenant_id, 7, NOW)["daily"]}
    assert daily["2026-10-18"]["checks"] == 1 and daily["2026-10-17"]["checks"] == 0
    assert daily["2026-10-18"]["flagged"] == 1


def test_other_tenants_data_is_never_included(db, record, make_tenant):
    actor, add = record
    add("mine", "WILL_FAIL", NOW - timedelta(days=1))
    assert overview(db, make_tenant("Other").id, 30, NOW)["claims"] == 0


@pytest.mark.parametrize(
    ("role", "status"), [(Role.CLERK, 403), (Role.FINANCE_MANAGER, 200), (Role.ADMIN, 200)]
)
def test_only_finance_roles_can_read_the_overview(client, make_user, login, role, status):
    session = login(make_user(f"{role}@x.test", role=role))
    assert session.get("/v1/reports/overview").status_code == status


def test_overview_requires_a_session_and_a_sane_window(client, make_user, login):
    assert client.get("/v1/reports/overview").status_code == 401
    session = login(make_user("a@x.test", role=Role.ADMIN))
    assert session.get("/v1/reports/overview", params={"days": 0}).status_code == 422
    assert session.get("/v1/reports/overview", params={"days": 366}).status_code == 422
    body = session.get("/v1/reports/overview", params={"days": 7}).json()
    assert body["days"] == 7 and len(body["daily"]) in {7, 8}
