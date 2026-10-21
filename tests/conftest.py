import os
from collections.abc import Iterator

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://hakiki:hakiki-dev@127.0.0.1:5433/hakiki_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["HMAC_KEY"] = "test-hmac-key"
os.environ["COOKIE_SECURE"] = "false"
os.environ["REDIS_URL"] = os.environ.get("TEST_REDIS_URL", "redis://127.0.0.1:6380/15")
os.environ["CORS_ORIGINS"] = '["http://localhost:5173"]'

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from api.db.models import Tenant, User  # noqa: E402
from api.main import app  # noqa: E402
from api.security import Role, hash_password  # noqa: E402

PASSWORD = "correct-horse-battery"


@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DATABASE_URL)
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))
    command.upgrade(Config("alembic.ini"), "head")
    yield engine
    engine.dispose()


@pytest.fixture(autouse=True)
def clean_redis():
    from api.ratelimit import get_redis

    get_redis().flushdb()


@pytest.fixture
def db(engine) -> Iterator[Session]:
    with Session(engine, expire_on_commit=False) as session:
        yield session
    with engine.begin() as connection:
        connection.execute(
            text(
                "TRUNCATE claims_checked, audit_log, sessions, users, tenants "
                "RESTART IDENTITY CASCADE"
            )
        )


@pytest.fixture
def client(db) -> TestClient:
    return TestClient(app)


@pytest.fixture
def make_tenant(db):
    def create(name: str = "Mercy Hospital") -> Tenant:
        tenant = Tenant(name=name)
        db.add(tenant)
        db.commit()
        return tenant

    return create


@pytest.fixture
def make_user(db, make_tenant):
    def create(
        email: str = "clerk@mercy.test",
        tenant: Tenant | None = None,
        role: Role = Role.CLERK,
        active: bool = True,
    ) -> User:
        user = User(
            tenant_id=(tenant or make_tenant()).id,
            email=email,
            name="Test User",
            password_hash=hash_password(PASSWORD),
            role=role.value,
            is_active=active,
        )
        db.add(user)
        db.commit()
        return user

    return create


@pytest.fixture
def login(client):
    def do_login(user: User) -> TestClient:
        response = client.post("/v1/auth/login", json={"email": user.email, "password": PASSWORD})
        assert response.status_code == 200
        return client

    return do_login


@pytest.fixture
def claim() -> dict:
    return {
        "claim_ref": "clm-104",
        "patient_token": "pat-abc",
        "facility_id": "fac-12",
        "service_code": "svc-CS-01",
        "fund": "SHIF",
        "date_of_service": "2026-10-14",
        "amount_kes": 45000,
        "preauth_ref": None,
        "icd_code": "O82",
    }


@pytest.fixture
def result() -> dict:
    return {
        "claim": "clm-104",
        "verdict": "WILL_FAIL",
        "truth_value": {"strength": 0.95, "confidence": 0.92},
        "revenue_at_risk_kes": 45000,
        "trace": [{"step": 1, "rule": "R3-MissingPreauth", "result": "fail", "stv": [0.95, 0.92]}],
        "fixes": [{"action": "Attach pre-authorisation reference", "flips_to": "PASS"}],
        "rulebook_version": "sha-rules-2026.10.1",
    }
