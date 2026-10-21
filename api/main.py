from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from api.config import get_settings
from api.db.session import get_engine
from api.errors import install_error_handlers
from api.limits import BodySizeLimit
from api.logging_config import RequestLog, setup_logging
from api.routes import (
    api_keys,
    audit,
    auth,
    batch,
    citations,
    claims,
    history,
    reference,
    reports,
    users,
)
from api.services.batches import fail_stale_batches


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    with Session(get_engine()) as db:
        fail_stale_batches(db)
    yield


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="Hakiki API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Total-Count", "X-Request-ID"],
    )
    app.add_middleware(BodySizeLimit, upload_prefixes=("/v1/claims/batch",))
    app.add_middleware(RequestLog)
    install_error_handlers(app)
    for module in (
        auth,
        api_keys,
        batch,
        claims,
        history,
        citations,
        reference,
        reports,
        audit,
        users,
    ):
        app.include_router(module.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
