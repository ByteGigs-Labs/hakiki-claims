import os
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from api.db.models import ClaimChecked, Tenant, User
from api.db.session import get_engine
from api.security import Principal, Role, hash_password
from api.services.checks import check_and_record
from ingest.csv_import import parse_csv

SYNTHETIC_CLAIMS = Path(__file__).resolve().parent.parent / "data" / "synthetic" / "claims.csv"
SEED_MAX_ROWS = 1000


def ensure_demo_user(db: Session) -> User:
    tenant_name = os.environ["DEMO_TENANT_NAME"]
    email = os.environ["DEMO_USER_EMAIL"].strip().lower()
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
            name=os.environ["DEMO_USER_NAME"],
            password_hash=hash_password(os.environ["DEMO_USER_PASSWORD"]),
            role=Role.ADMIN,
        )
        db.add(user)
    db.commit()
    return user


def load_synthetic_claims(db: Session, user: User) -> int:
    already_loaded = db.scalar(
        select(func.count())
        .select_from(ClaimChecked)
        .where(ClaimChecked.tenant_id == user.tenant_id)
    )
    if already_loaded:
        return 0
    principal = Principal(user.id, user.tenant_id, user.name, "", Role(user.role))
    parsed = parse_csv(SYNTHETIC_CLAIMS.read_bytes(), SEED_MAX_ROWS)
    for item in parsed.claims:
        check_and_record(db, principal, item["claim"], row_number=item["row"])
    db.commit()
    return len(parsed.claims)


if __name__ == "__main__":
    with Session(get_engine()) as session:
        load_synthetic_claims(session, ensure_demo_user(session))
