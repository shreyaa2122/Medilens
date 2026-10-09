"""Reads PDFs with PyMuPDF: embedded text when it exists, page images when it does not."""
import numpy as np
import pymupdf

from app.services.processing_errors import ProcessingError
from app.services.text_layout import LayoutWord, words_to_lines

MAX_RENDER_SIDE_PIXELS = 4000


class PdfDocument:
    """Use as a context manager so the file is always closed."""

    def __init__(self, content: bytes, max_pages: int):
        try:
            self._doc = pymupdf.open(stream=content, filetype="pdf")
        except Exception:
            raise ProcessingError("unreadable_document")

        if self._doc.needs_pass:
            self._doc.close()
            raise ProcessingError("password_protected_pdf")
        if self._doc.page_count == 0:
            self._doc.close()
            raise ProcessingError("unreadable_document")
        if self._doc.page_count > max_pages:
            self._doc.close()
            raise ProcessingError("too_many_pages")

    @property
    def page_count(self) -> int:
        return self._doc.page_count

    def native_text(self, page_index: int) -> str:
        """Text stored inside the PDF, with table rows kept together on one line."""
        try:
            raw_words = self._doc[page_index].get_text("words")
        except Exception:
            raise ProcessingError("unreadable_document")
        words = [LayoutWord(w[0], w[1], w[2], w[3], w[4]) for w in raw_words]
        return "\n".join(words_to_lines(words))

    def render_page(self, page_index: int, dpi: int) -> np.ndarray:
        """Draw the page as a grayscale image so it can be sent to OCR."""
        try:
            page = self._doc[page_index]
            longest_side_inches = max(page.rect.width, page.rect.height) / 72
            dpi = max(72, min(dpi, int(MAX_RENDER_SIDE_PIXELS / longest_side_inches)))
            pixmap = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY, alpha=False)
            rows = np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(pixmap.height, pixmap.stride)
            return rows[:, : pixmap.width].copy()
        except Exception:
            raise ProcessingError("unreadable_document")

    def close(self) -> None:
        self._doc.close()

    def __enter__(self) -> "PdfDocument":
        return self

    def __exit__(self, *_exc) -> None:
        self.close()
