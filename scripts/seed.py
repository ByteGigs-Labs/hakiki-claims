import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from api.db.models import Tenant, User
from api.db.session import get_engine
from api.security import Role, hash_password


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


if __name__ == "__main__":
    with Session(get_engine()) as session:
        ensure_demo_user(session)
