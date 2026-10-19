from datetime import UTC, datetime, timedelta
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.config import Settings
from api.db.models import ClaimChecked, Tenant, User
from api.db.session import get_engine
from api.security import Principal, Role, hash_password
from api.services.checks import check_and_record
from ingest.csv_import import parse_csv

SYNTHETIC_CLAIMS = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "claims.csv"
SEED_MAX_ROWS = 1000
SEED_SPAN_DAYS = 28
SEED_FIXED_CLAIMS = 8


def ensure_demo_user(db: Session) -> User:
    settings = Settings()
    if settings.demo_user_password is None:
        raise SystemExit("Set DEMO_USER_PASSWORD before seeding")
    tenant_name = settings.demo_tenant_name
    email = settings.demo_user_email.strip().lower()
    tenant = db.scalar(select(Tenant).where(Tenant.name == tenant_name))
    if not tenant:
        tenant = Tenant(name=tenant_name)
        db.add(tenant)
        db.flush()
    user = db.scalar(select(User).where(User.email == email))
    if not user:
        user = User(
            tenant_id=tenant.id,
            email=email,
            name=settings.demo_user_name,
            password_hash=hash_password(settings.demo_user_password.get_secret_value()),
            role=Role.ADMIN,
        )
        db.add(user)
    db.commit()
    return user


def load_synthetic_claims(db: Session, user: User, now: datetime | None = None) -> int:
    already_loaded = db.scalar(
        select(func.count())
        .select_from(ClaimChecked)
        .where(ClaimChecked.tenant_id == user.tenant_id)
    )
    if already_loaded:
        return 0
    now = (now or datetime.now(UTC)).replace(hour=7, minute=0, second=0, microsecond=0)
    principal = Principal(user.id, user.tenant_id, user.name, "", Role(user.role))
    claims = parse_csv(SYNTHETIC_CLAIMS.read_bytes(), SEED_MAX_ROWS).claims
    fixed = 0
    for index, item in enumerate(claims):
        age = timedelta(days=SEED_SPAN_DAYS * (len(claims) - index) // len(claims))
        checked_at = now - age + timedelta(minutes=index)
        result = check_and_record(
            db, principal, item["claim"], row_number=item["row"], checked_at=checked_at
        )
        if result["verdict"] != "PASS" and result["fixes"] and fixed < SEED_FIXED_CLAIMS:
            patch = {key: value for fix in result["fixes"] for key, value in fix["patch"].items()}
            repaired = check_and_record(
                db,
                principal,
                {**item["claim"], **patch},
                checked_at=checked_at + timedelta(hours=2),
            )
            fixed += repaired["verdict"] == "PASS"
    db.commit()
    return len(claims)


if __name__ == "__main__":
    with Session(get_engine()) as session:
        load_synthetic_claims(session, ensure_demo_user(session))
