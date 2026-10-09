"""Validates an uploaded file before anything is stored.

We check three things: the file is not empty, it is not too large, and its real
content (not just its name) is a PDF, PNG or JPEG.
"""
import os
from dataclasses import dataclass

from app.core.errors import AppError

SUPPORTED_TYPES_MESSAGE = "Unsupported file type. Please upload a PDF, JPG, JPEG, or PNG."

# Maps the file extension a user typed to the kind of file it claims to be.
EXTENSION_TO_KIND = {"pdf": "pdf", "png": "png", "jpg": "jpeg", "jpeg": "jpeg"}

# For each kind: the extension we store, the MIME type, and the starting bytes
# ("magic bytes") that every genuine file of that kind begins with.
KIND_DETAILS = {
    "pdf": {"extension": "pdf", "mime_type": "application/pdf", "signature": b"%PDF-"},
    "png": {"extension": "png", "mime_type": "image/png", "signature": b"\x89PNG\r\n\x1a\n"},
    "jpeg": {"extension": "jpg", "mime_type": "image/jpeg", "signature": b"\xff\xd8\xff"},
}


@dataclass(frozen=True)
class ValidatedFile:
    extension: str
    mime_type: str
    size_bytes: int


def detect_kind_from_content(content: bytes) -> str | None:
    for kind, details in KIND_DETAILS.items():
        if content.startswith(details["signature"]):
            return kind
    return None


def validate_upload(filename: str, content: bytes, max_bytes: int) -> ValidatedFile:
    if len(content) == 0:
        raise AppError("empty_file", "The file is empty. Please choose a file that contains a document.", 400)

    if len(content) > max_bytes:
        max_mb = max_bytes // (1024 * 1024)
        raise AppError(
            "file_too_large", f"The file is larger than {max_mb} MB. Please upload a smaller file.", 413
        )

    claimed_extension = os.path.splitext(filename)[1].lstrip(".").lower()
    claimed_kind = EXTENSION_TO_KIND.get(claimed_extension)
    if claimed_kind is None:
        raise AppError("unsupported_file_type", SUPPORTED_TYPES_MESSAGE, 415)

    actual_kind = detect_kind_from_content(content)
    if actual_kind is None:
        raise AppError("unsupported_file_type", SUPPORTED_TYPES_MESSAGE, 415)

    if actual_kind != claimed_kind:
        raise AppError(
            "file_content_mismatch",
            "The file's contents do not match its file extension. Please upload a genuine PDF, JPG, JPEG, or PNG.",
            415,
        )

    details = KIND_DETAILS[actual_kind]
    return ValidatedFile(
        extension=details["extension"],
        mime_type=details["mime_type"],
        size_bytes=len(content),
    )
