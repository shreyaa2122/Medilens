import pytest

from app.services.ocr_service import OcrService
from app.services.processing_errors import ProcessingError
from app.services.text_extraction_service import extract_document_text
from tests.sample_documents import (
    blur,
    make_blank_pdf,
    make_digital_pdf,
    make_scanned_pdf,
    render_report,
    to_jpeg_bytes,
    to_png_bytes,
    words_found,
)
from tests.test_ocr_service import TOTAL_WORDS, requires_tesseract


class OcrThatMustNotBeUsed:
    def read_image(self, _image):
        raise AssertionError("OCR was called for a document that already contains text")


def extract(content, mime, ocr=None, min_chars=100, max_pages=20):
    return extract_document_text(content, mime, ocr or OcrService(), min_chars, max_pages)


def test_digital_pdf_is_read_directly_without_ocr():
    pages = extract(make_digital_pdf(), "application/pdf", ocr=OcrThatMustNotBeUsed())
    assert len(pages) == 1
    assert pages[0].method == "native"
    assert pages[0].ocr_confidence is None
    assert pages[0].page_number == 1
    assert words_found(pages[0].text) == TOTAL_WORDS


def test_blank_pdf_reports_no_text_found():
    class BlankOcr:
        def read_image(self, _image):
            from app.services.ocr_service import EMPTY_RESULT
            return EMPTY_RESULT

    with pytest.raises(ProcessingError) as error:
        extract(make_blank_pdf(), "application/pdf", ocr=BlankOcr())
    assert error.value.code == "no_text_found"


def test_scanned_page_is_sent_to_ocr():
    seen = []

    class RecordingOcr:
        def read_image(self, image):
            from app.services.ocr_service import OcrResult
            seen.append(image.shape)
            return OcrResult("Hemoglobin 10.2", 0.9, 14, 2)

    pages = extract(make_scanned_pdf(render_report()), "application/pdf", ocr=RecordingOcr())
    assert len(seen) == 1
    assert pages[0].method == "ocr" and pages[0].ocr_confidence == 0.9


@requires_tesseract
def test_scanned_pdf_is_read_with_real_ocr():
    pages = extract(make_scanned_pdf(render_report()), "application/pdf")
    assert pages[0].method == "ocr"
    assert words_found(pages[0].text) >= TOTAL_WORDS - 1
    assert pages[0].ocr_confidence >= 0.8


@requires_tesseract
@pytest.mark.parametrize("encode, mime", [(to_png_bytes, "image/png"), (to_jpeg_bytes, "image/jpeg")])
def test_photos_are_read_with_ocr(encode, mime):
    pages = extract(encode(render_report()), mime)
    assert pages[0].method == "ocr"
    assert words_found(pages[0].text) >= TOTAL_WORDS - 1


@requires_tesseract
def test_blurry_photo_is_flagged_as_low_confidence_or_unreadable():
    blurry = to_png_bytes(blur(render_report(), sigma=4))
    try:
        pages = extract(blurry, "image/png")
    except ProcessingError as error:
        assert error.code == "no_text_found"
    else:
        assert pages[0].ocr_confidence < 0.70


def test_corrupt_image_is_unreadable():
    with pytest.raises(ProcessingError) as error:
        extract(b"\xff\xd8\xff\xe0" + b"junk" * 50, "image/jpeg", ocr=OcrThatMustNotBeUsed())
    assert error.value.code == "unreadable_document"
