import io
import json
import logging

import pytest
from fastapi.testclient import TestClient

from api.logging_config import JsonFormatter, RedactFilter, redact, setup_logging

from .test_batch import HEADER, row, upload
from .test_check_api import BODY

IDENTIFIER = "NATIONAL-ID-99887766"


@pytest.fixture
def lines():
    stream = io.StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactFilter())
    logging.getLogger().addHandler(handler)
    logging.getLogger().setLevel(logging.DEBUG)
    yield lambda: [json.loads(line) for line in stream.getvalue().splitlines()]
    logging.getLogger().removeHandler(handler)


def with_identifier(**extra) -> dict:
    body = {key: value for key, value in BODY.items() if key != "patient_token"}
    return {**body, "patient_id": IDENTIFIER, **extra}


def test_every_response_carries_a_request_id(client, make_user, login):
    session = login(make_user())
    ids = {
        client.get("/health").headers["X-Request-ID"],
        session.get("/v1/auth/me").headers["X-Request-ID"],
        client.get("/v1/claims").headers["X-Request-ID"],
        session.post("/v1/claims/check", json={}).headers["X-Request-ID"],
    }
    assert len(ids) == 4 and all(len(value) == 32 for value in ids)


def test_request_lines_are_structured_and_drop_the_query_string(client, lines):
    client.get("/health?secret=abc")
    entry = next(item for item in lines() if item["logger"] == "hakiki.request")
    assert entry["method"] == "GET" and entry["path"] == "/health" and entry["status"] == 200
    assert entry["duration_ms"] >= 0 and len(entry["request_id"]) == 32


def test_patient_identifiers_never_reach_the_logs(client, make_user, login, lines):
    session = login(make_user())
    assert session.post("/v1/claims/check", json=with_identifier()).status_code == 200
    assert session.post("/v1/claims/check", json=with_identifier(amount_kes="x")).status_code == 422
    csv = HEADER + row(patient=IDENTIFIER) + row(ref="bad", patient=IDENTIFIER, amount="oops")
    assert upload(session, csv).status_code == 202
    assert IDENTIFIER not in json.dumps(lines())


def test_validation_failures_log_field_names_only(client, make_user, login, lines):
    login(make_user()).post("/v1/claims/check", json=with_identifier(amount_kes=IDENTIFIER))
    text = json.dumps(lines())
    assert "amount_kes" in text and IDENTIFIER not in text


def test_server_errors_log_the_exception_type_not_the_body(
    client, make_user, login, lines, monkeypatch
):
    from api.routes import claims

    def explode(*_args, **_kwargs):
        raise RuntimeError(f"failed for {IDENTIFIER}")

    monkeypatch.setattr(claims, "check_and_record", explode)
    session = login(make_user())
    probe = TestClient(client.app, raise_server_exceptions=False, cookies=session.cookies)
    response = probe.post("/v1/claims/check", json=with_identifier())
    assert response.status_code == 500 and len(response.headers["X-Request-ID"]) == 32
    records = lines()
    assert any("RuntimeError" in json.dumps(item) for item in records)
    assert IDENTIFIER not in json.dumps(records)


@pytest.mark.parametrize(
    "text",
    [
        "Authorization: Bearer abc.def-123",
        "hk_abcd1234_" + "x" * 32,
        "cookie hakiki_session=" + "a" * 43,
        '{"password": "hunter2hunter2"}',
        "id " + "Z" * 40,
    ],
)
def test_secret_shapes_are_redacted(text):
    cleaned = redact(text)
    for secret in ("abc.def-123", "abcd1234", "hunter2", "a" * 43, "Z" * 40):
        assert secret not in cleaned


def test_ordinary_messages_survive_redaction():
    assert redact("request on /v1/claims returned 200") == "request on /v1/claims returned 200"


def test_setup_is_idempotent():
    setup_logging()
    setup_logging()
    assert len(logging.getLogger().handlers) == 1
