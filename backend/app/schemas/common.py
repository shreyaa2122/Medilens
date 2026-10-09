"""Shared response shapes so every endpoint returns the same JSON envelope.

Success: {"data": {...}, "error": null}
Failure: {"data": null, "error": {"code": "...", "message": "..."}}
"""
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[dict[str, str]] | None = None


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    error: ErrorBody | None = None


class HealthStatus(BaseModel):
    status: str
    service: str
    version: str
    environment: str
