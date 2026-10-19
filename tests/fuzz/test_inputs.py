from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st
from pydantic import ValidationError

from api.config import get_settings
from ingest.claim_schema import ClaimInput
from ingest.csv_import import CsvImportError, ParsedBatch, parse_csv

FUZZ = settings(
    max_examples=150,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.function_scoped_fixture],
)
JSON_VALUES = st.recursive(
    st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=30),
    lambda children: (
        st.lists(children, max_size=4) | st.dictionaries(st.text(max_size=12), children, max_size=5)
    ),
    max_leaves=12,
)


@FUZZ
@given(content=st.binary(max_size=600))
def test_csv_parser_only_raises_its_own_error(content):
    try:
        parsed = parse_csv(content, 50)
    except CsvImportError:
        return
    assert isinstance(parsed, ParsedBatch) and parsed.total >= 1


@FUZZ
@given(body=st.text(max_size=400))
def test_csv_parser_survives_arbitrary_text_with_a_valid_header(body):
    header = "facility_id,service_code,fund,date_of_service,amount_kes,patient_id\n"
    try:
        parse_csv((header + body).encode(), 50)
    except CsvImportError:
        pass


@FUZZ
@given(payload=st.dictionaries(st.text(max_size=15), JSON_VALUES, max_size=8))
def test_claim_schema_only_raises_validation_errors(payload):
    try:
        ClaimInput.model_validate(payload).to_claim()
    except ValidationError:
        pass


@settings(FUZZ, max_examples=60)
@given(payload=JSON_VALUES)
def test_check_endpoint_never_returns_a_server_error(
    client, make_user, login, monkeypatch, payload
):
    monkeypatch.setattr(get_settings(), "check_per_minute", 10**6)
    session = client if client.cookies else login(make_user())
    response = session.post("/v1/claims/check", json=payload)
    assert response.status_code in {200, 422}


@settings(FUZZ, max_examples=60)
@given(
    sort=st.text(max_size=20),
    order=st.text(max_size=8),
    start=st.integers(-5, 500),
    end=st.integers(-5, 500),
)
def test_history_endpoint_rejects_bad_paging_without_failing(
    client, make_user, login, sort, order, start, end
):
    session = client if client.cookies else login(make_user())
    response = session.get(
        "/v1/claims", params={"_sort": sort, "_order": order, "_start": start, "_end": end}
    )
    assert response.status_code in {200, 422}
