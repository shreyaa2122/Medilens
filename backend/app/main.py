"""App entry point. Only wires things together; business logic lives in services/."""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents, health
from app.core.config import Settings, get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.db.models import Base
from app.db.session import create_db_engine, create_session_factory
from app.services.storage_service import StorageService
from app.services.user_service import ensure_default_user

logger = logging.getLogger("medilens.access")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(app.state.engine)
    with app.state.session_factory() as session:
        ensure_default_user(session)
    yield
    app.state.engine.dispose()


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)

    app.state.settings = settings
    app.state.engine = create_db_engine(settings.database_url)
    app.state.session_factory = create_session_factory(app.state.engine)
    app.state.storage = StorageService(settings.upload_dir)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        # Method, path and status only. No query strings, no bodies, no file names.
        logger.info("%s %s -> %s (%.0f ms)", request.method, request.url.path,
                    response.status_code, elapsed_ms)
        return response

    register_error_handlers(app)
    app.include_router(health.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    return app


app = create_app()
