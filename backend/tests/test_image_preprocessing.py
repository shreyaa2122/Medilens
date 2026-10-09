import numpy as np
import pytest

from app.services.image_preprocessing import (
    MAX_LONG_SIDE,
    TARGET_LONG_SIDE,
    clean_for_ocr,
    deskew,
    estimate_skew_angle,
    flatten_lighting,
    load_image,
    resize_for_ocr,
    rotate_clockwise,
    to_grayscale,
)
from app.services.processing_errors import ProcessingError
from tests.sample_documents import (
    add_uneven_lighting,
    render_report,
    rotate_small,
    to_jpeg_bytes,
    to_png_bytes,
)


def test_load_image_decodes_png_to_three_channels():
    image = load_image(to_png_bytes(render_report()))
    assert image.ndim == 3 and image.shape[2] == 3


def test_load_image_applies_phone_rotation_tag():
    page = render_report()                      # wider than tall
    upright = load_image(to_jpeg_bytes(page))
    rotated = load_image(to_jpeg_bytes(page, exif_orientation=6))  # "rotate 90 degrees to view"
    assert upright.shape[0] < upright.shape[1]
    assert rotated.shape[0] > rotated.shape[1]  # width and height swapped


def test_load_image_rejects_garbage_bytes():
    with pytest.raises(ProcessingError) as error:
        load_image(b"\x89PNG\r\n\x1a\n" + b"not really an image" * 20)
    assert error.value.code == "unreadable_document"


def test_load_image_rejects_huge_dimensions(monkeypatch):
    monkeypatch.setattr("app.services.image_preprocessing.MAX_IMAGE_PIXELS", 100)
    with pytest.raises(ProcessingError) as error:
        load_image(to_png_bytes(render_report()))
    assert error.value.code == "image_too_large"


def test_to_grayscale_handles_color_and_gray():
    color = np.zeros((10, 10, 3), dtype=np.uint8)
    assert to_grayscale(color).ndim == 2
    gray = np.zeros((10, 10), dtype=np.uint8)
    assert to_grayscale(gray) is gray


def test_resize_enlarges_small_and_shrinks_huge_images():
    small = np.full((300, 200), 255, dtype=np.uint8)
    assert max(resize_for_ocr(small).shape) > 300
    huge = np.full((MAX_LONG_SIDE + 2000, 1000), 255, dtype=np.uint8)
    assert max(resize_for_ocr(huge).shape) == MAX_LONG_SIDE
    ok_size = np.full((TARGET_LONG_SIDE + 100, 1000), 255, dtype=np.uint8)
    assert resize_for_ocr(ok_size).shape == ok_size.shape


def test_rotate_clockwise_swaps_dimensions_for_quarter_turns():
    image = np.zeros((100, 200), dtype=np.uint8)
    assert rotate_clockwise(image, 90).shape == (200, 100)
    assert rotate_clockwise(image, 180).shape == (100, 200)
    assert rotate_clockwise(image, 0) is image


@pytest.mark.parametrize("tilt", [4.0, -7.0, 0.0])
def test_skew_angle_is_estimated_within_one_degree(tilt):
    tilted = rotate_small(render_report(), tilt)
    # The estimate is the correction to apply, so it has the opposite sign of the tilt.
    assert abs(estimate_skew_angle(tilted) + tilt) <= 1.0


def test_deskew_leaves_straight_pages_untouched():
    page = render_report()
    assert deskew(page) is page


def test_skew_detection_survives_uneven_lighting():
    tilted = add_uneven_lighting(rotate_small(render_report(), 4.0), darkest=0.4)
    assert abs(estimate_skew_angle(tilted) + 4.0) <= 1.0


def test_flatten_lighting_evens_out_the_background():
    shaded = add_uneven_lighting(render_report(), darkest=0.4)
    flat = flatten_lighting(shaded)

    def background_gap(image):
        # Bottom rows contain no text, so they show the paper itself.
        return abs(float(np.median(image[-50:, :200])) - float(np.median(image[-50:, -200:])))

    assert background_gap(shaded) > 80   # clearly uneven before
    assert background_gap(flat) < 15     # nearly even after


def test_clean_for_ocr_keeps_shape_and_type():
    page = render_report()
    cleaned = clean_for_ocr(page)
    assert cleaned.shape == page.shape and cleaned.dtype == np.uint8
