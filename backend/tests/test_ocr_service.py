import numpy as np
import pytest

from app.services.ocr_service import OcrService
from app.services.processing_errors import ProcessingError
from tests.sample_documents import (
    add_noise,
    add_uneven_lighting,
    blur,
    render_report,
    rotate_quarter,
    rotate_small,
    words_found,
)

ocr = OcrService()
requires_tesseract = pytest.mark.skipif(
    not ocr.is_available(), reason="Tesseract is not installed on this machine"
)
TOTAL_WORDS = 7  # len(EXPECTED_WORDS)


def test_missing_tesseract_is_reported_cleanly():
    missing = OcrService(tesseract_cmd="/definitely/not/tesseract")
    assert missing.is_available() is False
    with pytest.raises(ProcessingError) as error:
        missing.read_image(render_report())
    assert error.value.code == "ocr_unavailable"


@requires_tesseract
def test_clean_scan_is_read_with_high_confidence():
    result = ocr.read_image(render_report())
    assert words_found(result.text) == TOTAL_WORDS
    assert result.confidence >= 0.85
    assert "Hemoglobin" in result.text and "10.2" in result.text


@requires_tesseract
def test_table_rows_stay_together():
    lines = ocr.read_image(render_report()).text.splitlines()
    hemoglobin_line = next(line for line in lines if "Hemoglobin" in line)
    assert "10.2" in hemoglobin_line and "g/dL" in hemoglobin_line


@requires_tesseract
@pytest.mark.parametrize("turn", [90, 180, 270])
def test_sideways_and_upside_down_pages_are_turned_upright(turn):
    result = ocr.read_image(rotate_quarter(render_report(), turn))
    assert words_found(result.text) >= TOTAL_WORDS - 1


@requires_tesseract
def test_slightly_crooked_photo_is_straightened():
    result = ocr.read_image(rotate_small(render_report(), 5))
    assert words_found(result.text) >= TOTAL_WORDS - 1


@requires_tesseract
def test_noisy_image_is_cleaned_and_read():
    result = ocr.read_image(add_noise(render_report(), strength=40))
    assert words_found(result.text) >= TOTAL_WORDS - 1


@requires_tesseract
def test_uneven_lighting_is_corrected():
    # This image reads almost nothing without the stronger clean-up pass.
    result = ocr.read_image(add_uneven_lighting(render_report(), darkest=0.4))
    assert words_found(result.text) >= TOTAL_WORDS - 2


@requires_tesseract
def test_blurry_image_reports_low_confidence_instead_of_pretending():
    clean = ocr.read_image(render_report())
    blurry = ocr.read_image(blur(render_report(), sigma=4))
    assert blurry.confidence < 0.70           # the UI will tell the user to verify
    assert blurry.confidence < clean.confidence
    assert words_found(blurry.text) < TOTAL_WORDS


@requires_tesseract
def test_blank_page_gives_empty_text():
    result = ocr.read_image(np.full((600, 800), 255, dtype=np.uint8))
    assert result.text == ""
    assert result.confidence == 0.0
