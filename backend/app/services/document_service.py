"""Business logic for uploaded documents. Routes call these; they hold no logic."""
import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import sanitize_filename
from app.db.models import Document, User
from app.services.file_validation import validate_upload
from app.services.storage_service import StorageService

logger = logging.getLogger(__name__)


def register_upload(
    db: Session,
    storage: StorageService,
    user: User,
    filename: str | None,
    content: bytes,
    max_bytes: int,
) -> Document:
    safe_name = sanitize_filename(filename)
    validated = validate_upload(safe_name, content, max_bytes)

    stored_name = storage.save(content, validated.extension)
    document = Document(
        user_id=user.id,
        file_name=safe_name,
        stored_name=stored_name,
        mime_type=validated.mime_type,
        file_size_bytes=validated.size_bytes,
    )
    try:
        db.add(document)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        storage.delete(stored_name)  # do not leave an orphaned file behind
        logger.error("Could not save document record: %s", type(exc).__name__)
        raise AppError("database_error", "We could not save your document. Please try again.", 500)
    return document


def list_documents(db: Session, user: User) -> list[Document]:
    query = select(Document).where(Document.user_id == user.id).order_by(Document.upload_date.desc())
    return list(db.scalars(query))


def get_document(db: Session, user: User, document_id: uuid.UUID) -> Document:
    document = db.get(Document, document_id)
    if document is None or document.user_id != user.id:
        raise AppError("document_not_found", "That document could not be found.", 404)
    return document


def delete_document(db: Session, storage: StorageService, document: Document) -> None:
    # File first: if the database step fails the user can simply retry.
    storage.delete(document.stored_name)
    try:
        db.delete(document)
        db.commit()
    except SQLAlchemyError as exc:
        db.rollback()
        logger.error("Could not delete document record: %s", type(exc).__name__)
        raise AppError("database_error", "We could not delete the document. Please try again.", 500)
