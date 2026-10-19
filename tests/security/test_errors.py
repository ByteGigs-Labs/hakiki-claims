def body(**overrides) -> dict:
    return {
        "patient_token": "pat-1",
        "facility_id": "fac-12",
        "service_code": "svc-OPD-01",
        "fund": "SHIF",
        "date_of_service": "2026-10-14",
        "amount_kes": 700,
        **overrides,
    }


def test_validation_errors_use_the_common_shape_and_never_echo_input(client, make_user, login):
    session = login(make_user())
    response = session.post("/v1/claims/check", json=body(service_code="<script>alert(1)</script>"))
    payload = response.json()
    assert response.status_code == 422
    assert payload["error"]["code"] == "validation_error"
    assert payload["error"]["fields"][0]["field"] == "service_code"
    assert "script" not in response.text


def test_unknown_routes_and_methods_use_the_common_shape(client):
    missing = client.get("/v1/nope")
    wrong_method = client.put("/health")
    assert (missing.status_code, missing.json()["error"]["code"]) == (404, "http_error")
    assert wrong_method.status_code == 405 and "error" in wrong_method.json()


def test_unauthenticated_errors_use_the_common_shape(client):
    response = client.get("/v1/claims")
    assert (
        response.status_code == 401 and response.json()["error"]["message"] == "Not authenticated"
    )


def test_unexpected_failures_return_a_generic_500_without_internals(
    client, make_user, login, monkeypatch
):
    from api.routes import claims

    def explode(*_args, **_kwargs):
        raise RuntimeError("secret database password in message")

    monkeypatch.setattr(claims, "check_and_record", explode)
    session = login(make_user())
    session.raise_server_exceptions = False
    response = type(client)(
        client.app, raise_server_exceptions=False, cookies=session.cookies
    ).post("/v1/claims/check", json=body())
    assert response.status_code == 500
    assert response.json() == {"error": {"code": "server_error", "message": "Something went wrong"}}
    assert "secret" not in response.text and "Traceback" not in response.text


def test_extra_fields_are_rejected(client, make_user, login):
    assert login(make_user()).post("/v1/claims/check", json=body(is_admin=True)).status_code == 422
