"""Runs the processing steps for one document, in the background after upload.

Steps so far: read the file -> extract text (native PDF text or OCR) -> save the pages.
The document's status tells the user where things stand. Failures are stored as a short
error code; the user sees a safe message, and nothing from the document is logged.
"""
import logging
import uuid

from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.db.models import Document, DocumentPage
from app.services.ocr_service import OcrService
from app.services.processing_errors import ProcessingError
from app.services.storage_service import StorageService
from app.services.text_extraction_service import extract_document_text

logger = logging.getLogger(__name__)


def process_document(
    document_id: uuid.UUID,
    session_factory: sessionmaker[Session],
    storage: StorageService,
    ocr: OcrService,
    settings: Settings,
) -> None:
    with session_factory() as db:
        document = db.get(Document, document_id)
        if document is None:
            return  # deleted before processing started

        document.processing_status = "processing"
        document.error_code = None
        db.commit()

        try:
            content = storage.read(document.stored_name)
            pages = extract_document_text(
                content,
                document.mime_type,
                ocr,
                min_native_chars=settings.ocr_min_native_text_chars,
                max_pdf_pages=settings.max_pdf_pages,
            )
            document.pages = [
                DocumentPage(
                    page_number=page.page_number,
                    text=page.text,
                    method=page.method,
                    ocr_confidence=page.ocr_confidence,
                )
                for page in pages
            ]
            document.processing_status = "completed"
            db.commit()
            logger.info("Processed document %s (%d pages)", document_id, len(pages))
        except ProcessingError as error:
            _mark_failed(db, document_id, error.code)
        except FileNotFoundError:
            _mark_failed(db, document_id, "file_missing")
        except Exception as error:  # never let a background task crash silently
            logger.error("Unexpected processing error: %s", type(error).__name__)
            _mark_failed(db, document_id, "internal_error")


def _mark_failed(db: Session, document_id: uuid.UUID, code: str) -> None:
    db.rollback()
    document = db.get(Document, document_id)
    if document is None:
        return
    document.pages = []
    document.processing_status = "failed"
    document.error_code = code
    db.commit()
    logger.warning("Document %s failed: %s", document_id, code)
