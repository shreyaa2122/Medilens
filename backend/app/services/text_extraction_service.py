"""Turns an uploaded file into text, page by page.

PDFs: use the text stored inside the PDF when a page has enough of it. Pages that have
little or no embedded text are scans, so they are drawn as images and sent to OCR.
Images: always go through OCR.
"""
from dataclasses import dataclass
from typing import Literal

from app.services.image_preprocessing import load_image
from app.services.ocr_service import OcrService
from app.services.pdf_service import PdfDocument
from app.services.processing_errors import ProcessingError

OCR_RENDER_DPI = 200


@dataclass(frozen=True)
class PageText:
    page_number: int  # starts at 1
    text: str
    method: Literal["native", "ocr"]
    ocr_confidence: float | None  # only set for OCR pages


def extract_document_text(
    content: bytes,
    mime_type: str,
    ocr: OcrService,
    min_native_chars: int,
    max_pdf_pages: int,
) -> list[PageText]:
    if mime_type == "application/pdf":
        pages = _extract_from_pdf(content, ocr, min_native_chars, max_pdf_pages)
    else:
        pages = _extract_from_image(content, ocr)

    if not any(page.text.strip() for page in pages):
        raise ProcessingError("no_text_found")
    return pages


def _extract_from_pdf(
    content: bytes, ocr: OcrService, min_native_chars: int, max_pdf_pages: int
) -> list[PageText]:
    pages: list[PageText] = []
    with PdfDocument(content, max_pdf_pages) as pdf:
        for index in range(pdf.page_count):
            native_text = pdf.native_text(index)
            if len(native_text.strip()) >= min_native_chars:
                pages.append(PageText(index + 1, native_text, "native", None))
                continue

            # Too little embedded text: treat this page as a scan.
            result = ocr.read_image(pdf.render_page(index, OCR_RENDER_DPI))
            pages.append(PageText(index + 1, result.text, "ocr", result.confidence))
    return pages


def _extract_from_image(content: bytes, ocr: OcrService) -> list[PageText]:
    result = ocr.read_image(load_image(content))
    return [PageText(1, result.text, "ocr", result.confidence)]
