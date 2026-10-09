"""Custom errors and handlers.

Users only ever see clean messages. Stack traces and internal details
are never sent to the client.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """An error we raise on purpose, with a safe message for the user."""

    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def _error_response(
    status_code: int,
    code: str,
    message: str,
    details: list[dict[str, str]] | None = None,
) -> JSONResponse:
    body = {"data": None, "error": {"code": code, "message": message, "details": details}}
    return JSONResponse(status_code=status_code, content=body)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return _error_response(exc.status_code, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        # Only field names and generic issues are returned, never the submitted values.
        details = [
            {"field": ".".join(str(part) for part in err["loc"]), "issue": err["msg"]}
            for err in exc.errors()
        ]
        return _error_response(422, "invalid_request", "The request was not valid.", details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        if exc.status_code == 404:
            return _error_response(404, "not_found", "The requested resource was not found.")
        return _error_response(exc.status_code, "http_error", "The request could not be completed.")

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        # Log only the exception type: messages can contain document content.
        logger.error("Unhandled error: %s", type(exc).__name__)
        return _error_response(
            500, "internal_error", "Something went wrong on our side. Please try again."
        )
