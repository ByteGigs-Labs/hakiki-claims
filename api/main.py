from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.config import get_settings
from api.errors import install_error_handlers
from api.limits import BodySizeLimit
from api.routes import audit, auth, citations, claims, history


def create_app() -> FastAPI:
    app = FastAPI(title="Hakiki API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Total-Count"],
    )
    app.add_middleware(BodySizeLimit, upload_prefixes=("/v1/claims/batch",))
    install_error_handlers(app)
    for module in (auth, claims, history, citations, audit):
        app.include_router(module.router)

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
