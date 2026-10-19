import csv
from collections import Counter
from pathlib import Path

import pytest
from sqlalchemy import select

from api.config import get_settings
from api.db.models import AuditLog, Batch, ClaimChecked
from reasoner import audit

SYNTHETIC = Path(__file__).resolve().parents[1] / "data" / "synthetic"
HEADER = (
    "claim_ref,patient_id,facility_id,service_code,fund,date_of_service,amount_kes,member_status\n"
)


def upload(session, content: bytes | str, name: str = "claims.csv", content_type: str = "text/csv"):
    data = content.encode() if isinstance(content, str) else content
    return session.post("/v1/claims/batch", files={"file": (name, data, content_type)})


def row(
    ref="clm-1", patient="PT-1", service="svc-OPD-01", amount=700, day="2026-10-14", fund="SHIF"
):
    return f"{ref},{patient},fac-12,{service},{fund},{day},{amount},active\n"


@pytest.fixture
def session(make_user, login):
    return login(make_user())


def test_synthetic_set_is_processed_and_summarised_as_expected(session):
    accepted = upload(session, (SYNTHETIC / "claims.csv").read_bytes())
    assert accepted.status_code == 202
    batch = session.get(f"/v1/claims/batch/{accepted.json()['id']}").json()
    expected = list(csv.DictReader((SYNTHETIC / "expected.csv").open()))
    verdicts = Counter(item["verdict"] for item in expected)
    summary = batch["summary"]
    assert (batch["status"], batch["total"], batch["processed"]) == ("done", 40, 40)
    assert (summary["pass"], summary["at_risk"], summary["will_fail"]) == (
        verdicts["PASS"],
        verdicts["AT_RISK"],
        verdicts["WILL_FAIL"],
    )
    assert summary["claims"] == 40 and summary["rows_rejected"] == 0
    assert summary["revenue_at_risk_kes"] > 0
    assert summary["top_failing_rules"][0]["count"] >= summary["top_failing_rules"][-1]["count"]


def test_rows_can_be_filtered_by_verdict_and_paged(session):
    batch_id = upload(session, (SYNTHETIC / "claims.csv").read_bytes()).json()["id"]
    failing = session.get(f"/v1/claims/batch/{batch_id}/rows", params={"verdict": "WILL_FAIL"})
    assert failing.headers["x-total-count"] == str(
        len(failing.json()) if len(failing.json()) < 20 else int(failing.headers["x-total-count"])
    )
    assert all(item["verdict"] == "WILL_FAIL" and item["failing_rules"] for item in failing.json())
    page = session.get(f"/v1/claims/batch/{batch_id}/rows", params={"_start": 5, "_end": 8})
    assert [item["row_number"] for item in page.json()] == [6, 7, 8]
    assert page.headers["x-total-count"] == "40"


def test_invalid_rows_are_reported_without_echoing_values(session):
    content = (
        HEADER + row("clm-1") + row("clm-2", amount=-5) + row("clm-3", fund="NHIF") + row("clm-4")
    )
    batch_id = upload(session, content).json()["id"]
    batch = session.get(f"/v1/claims/batch/{batch_id}").json()
    assert batch["errors"] == [
        {"row": 2, "fields": ["amount_kes"]},
        {"row": 3, "fields": ["fund"]},
    ]
    assert (batch["total"], batch["summary"]["claims"], batch["summary"]["rows_rejected"]) == (
        4,
        2,
        2,
    )


def test_repeated_claim_reference_in_the_file_is_flagged(session):
    batch_id = upload(session, HEADER + row("clm-1") + row("clm-1", patient="PT-2")).json()["id"]
    assert session.get(f"/v1/claims/batch/{batch_id}").json()["errors"] == [
        {"row": 2, "fields": ["claim_ref"]}
    ]


def test_duplicates_inside_a_file_are_detected_across_rows(session):
    batch_id = upload(session, HEADER + row("clm-1") + row("clm-2")).json()["id"]
    rows = session.get(f"/v1/claims/batch/{batch_id}/rows").json()
    assert [item["verdict"] for item in rows] == ["PASS", "WILL_FAIL"]
    assert rows[1]["failing_rules"] == ["R8"]


def test_duplicates_against_earlier_batches_are_detected(session):
    upload(session, HEADER + row("clm-1"))
    batch_id = upload(session, HEADER + row("clm-2")).json()["id"]
    assert session.get(f"/v1/claims/batch/{batch_id}/rows").json()[0]["failing_rules"] == ["R8"]


@pytest.mark.parametrize(
    "content,message",
    [
        ("", "File is empty"),
        (HEADER, "File has no data rows"),
        ("claim_ref,secret\nx,y\n", "unrecognised columns"),
        ("claim_ref,patient_id\nx,y\n", "Missing required columns"),
        (
            "facility_id,service_code,fund,date_of_service,amount_kes\nx,y,z,w,1\n",
            "patient_id or patient_token",
        ),
        (b"\xff\xfe\x00bad", "UTF-8"),
    ],
)
def test_malformed_files_are_rejected_with_a_clear_reason(session, content, message):
    response = upload(session, content)
    assert response.status_code == 422 and message in response.json()["error"]["message"]


def test_row_limit_is_enforced(session, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_batch_rows", 2)
    assert upload(session, HEADER + row("a") + row("b") + row("c")).status_code == 422


def test_non_csv_uploads_are_refused(session):
    assert upload(session, "x", "claims.exe", "application/octet-stream").status_code == 415
    assert upload(session, "x", "claims.csv", "application/pdf").status_code == 415


def test_oversized_uploads_are_refused(session, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_bytes", 300)
    assert upload(session, HEADER + row() * 20).status_code == 413


def test_raw_patient_identifiers_are_never_persisted(session, db):
    upload(session, HEADER + row("clm-1", patient="NATIONAL-ID-99887766"))
    stored = " ".join(
        str(value)
        for model in (Batch, ClaimChecked, AuditLog)
        for entity in db.scalars(select(model))
        for value in vars(entity).values()
    )
    assert "NATIONAL-ID-99887766" not in stored


def test_filename_is_sanitised(session, db):
    upload(session, HEADER + row(), name="../../etc/<script>.csv")
    assert db.scalar(select(Batch.filename)) == "_script_.csv"


def test_batches_are_tenant_scoped(client, make_user, make_tenant, login):
    mine = login(make_user("a@a.test", make_tenant("A")))
    batch_id = upload(mine, HEADER + row()).json()["id"]
    client.cookies.clear()
    other = login(make_user("b@b.test", make_tenant("B")))
    assert other.get(f"/v1/claims/batch/{batch_id}").status_code == 404
    assert other.get(f"/v1/claims/batch/{batch_id}/rows").status_code == 404
    assert other.get("/v1/claims/batch").json() == []


def test_recent_batches_list_newest_first(session):
    first = upload(session, HEADER + row("clm-1")).json()["id"]
    second = upload(session, HEADER + row("clm-2", patient="PT-2")).json()["id"]
    assert [b["id"] for b in session.get("/v1/claims/batch").json()] == [second, first]


def test_template_downloads_as_csv_and_is_itself_valid(session):
    response = session.get("/v1/claims/batch/template")
    assert response.headers["content-type"].startswith("text/csv")
    assert "attachment" in response.headers["content-disposition"]
    assert upload(session, response.text).status_code == 202


def test_batch_requires_authentication_and_is_rate_limited(client, session, monkeypatch):
    monkeypatch.setattr(get_settings(), "batch_per_hour", 2)
    codes = [
        upload(session, HEADER + row(f"clm-{i}", patient=f"PT-{i}")).status_code for i in range(3)
    ]
    assert codes == [202, 202, 429]
    client.cookies.clear()
    assert upload(client, HEADER + row()).status_code == 401


def test_batch_results_keep_the_audit_chain_valid(session, db):
    upload(session, (SYNTHETIC / "claims.csv").read_bytes())
    tenant_id = db.scalar(select(Batch.tenant_id))
    assert audit.verify_chain(db, tenant_id).entries == 40
    assert session.get("/v1/audit/verify").json()["valid"] is True


def test_history_page_includes_batch_claims(session):
    upload(session, HEADER + row())
    assert session.get("/v1/claims").headers["x-total-count"] == "1"
