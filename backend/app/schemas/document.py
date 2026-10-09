import uuid
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    file_name: str
    mime_type: str
    file_size_bytes: int
    document_type: Literal["lab_report", "prescription", "unknown"]
    processing_status: Literal["uploaded", "processing", "completed", "failed"]
    overall_extraction_confidence: float | None
    upload_date: datetime

    @field_validator("upload_date")
    @classmethod
    def _assume_utc(cls, value: datetime) -> datetime:
        # SQLite returns naive datetimes; we always store UTC.
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
