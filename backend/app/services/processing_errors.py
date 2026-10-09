"""Errors raised while reading a document, with safe messages for the user.

The code is stored on the document; the message is looked up from it. Messages never
contain document content.
"""

PROCESSING_ERROR_MESSAGES: dict[str, str] = {
    "unreadable_document": "This document could not be opened. The file may be damaged.",
    "password_protected_pdf": "This PDF is password-protected. Please upload an unlocked copy.",
    "too_many_pages": "This PDF has too many pages to process. Please upload a shorter document.",
    "image_too_large": "This image is too large to process. Please upload a smaller photo or scan.",
    "no_text_found": (
        "No readable text was found in this document. "
        "Try a clearer, well-lit photo or a higher-quality scan."
    ),
    "ocr_unavailable": (
        "The text-reading engine (Tesseract) is not installed on the server, "
        "so scanned documents and photos cannot be read yet."
    ),
    "ocr_failed": "The text-reading engine failed on this document. Please try again.",
    "file_missing": "The stored file could not be found. Please upload the document again.",
    "interrupted": "Processing was interrupted. Please try again.",
    "internal_error": "Something went wrong while reading this document. Please try again.",
}


class ProcessingError(Exception):
    """Raised on purpose when a document cannot be processed."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


def message_for(code: str | None) -> str | None:
    if code is None:
        return None
    return PROCESSING_ERROR_MESSAGES.get(code, PROCESSING_ERROR_MESSAGES["internal_error"])
