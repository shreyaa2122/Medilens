"""FastAPI dependencies shared by routes."""
from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.core.errors import AppError
from app.db.models import User
from app.services.storage_service import StorageService
from app.services.user_service import DEFAULT_USER_ID


def get_app_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_storage(request: Request) -> StorageService:
    return request.app.state.storage


def get_db(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_current_user(db: Session = Depends(get_db)) -> User:
    """Single place that decides who is making the request.
    Today it always returns the default user. When login is added, only this
    function changes and every route is already access-controlled."""
    user = db.get(User, DEFAULT_USER_ID)
    if user is None:
        raise AppError("user_unavailable", "The service is not ready. Please try again.", 503)
    return user
