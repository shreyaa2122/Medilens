import pytest

from app.services.pdf_service import PdfDocument
from app.services.processing_errors import ProcessingError
from tests.sample_documents import (
    make_digital_pdf,
    make_password_protected_pdf,
    make_pdf_with_pages,
)


def test_native_text_keeps_each_table_row_on_one_line():
    with PdfDocument(make_digital_pdf(), max_pages=5) as pdf:
        lines = pdf.native_text(0).splitlines()
    assert "Hemoglobin  10.2  g/dL  12.0 - 16.0" in lines
    assert "Glucose  92  mg/dL  70 - 99" in lines


def test_page_count_and_render_shape():
    with PdfDocument(make_pdf_with_pages(3), max_pages=5) as pdf:
        assert pdf.page_count == 3
        image = pdf.render_page(0, dpi=100)
    assert image.ndim == 2
    assert 800 < image.shape[0] < 1300  # A4/Letter height at 100 dpi


def test_render_never_exceeds_the_pixel_cap():
    with PdfDocument(make_digital_pdf(), max_pages=5) as pdf:
        image = pdf.render_page(0, dpi=5000)
    assert max(image.shape) <= 4100


def test_garbage_is_unreadable():
    with pytest.raises(ProcessingError) as error:
        PdfDocument(b"%PDF-1.4 this is not a real pdf", max_pages=5)
    assert error.value.code == "unreadable_document"


def test_password_protected_pdf_is_rejected_with_clear_code():
    with pytest.raises(ProcessingError) as error:
        PdfDocument(make_password_protected_pdf(), max_pages=5)
    assert error.value.code == "password_protected_pdf"


def test_too_many_pages_is_rejected():
    with pytest.raises(ProcessingError) as error:
        PdfDocument(make_pdf_with_pages(6), max_pages=5)
    assert error.value.code == "too_many_pages"
