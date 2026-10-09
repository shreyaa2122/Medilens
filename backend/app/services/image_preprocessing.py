"""Image clean-up steps that help OCR read photos and scans.

Everything here works on numpy arrays and uses OpenCV. No text is read in this file.
"""
import io

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from app.services.processing_errors import ProcessingError

MAX_IMAGE_PIXELS = 40_000_000  # about 6300 x 6300; protects against decompression bombs
TARGET_LONG_SIDE = 2400        # OCR works best when text is reasonably large
MAX_LONG_SIDE = 3000         # about 250 DPI on an A4 page: plenty to read, and much faster


def load_image(content: bytes) -> np.ndarray:
    """Decode an uploaded image into a BGR array, applying the camera's rotation tag."""
    try:
        with Image.open(io.BytesIO(content)) as img:
            width, height = img.size  # reads only the header
            if width * height > MAX_IMAGE_PIXELS:
                raise ProcessingError("image_too_large")
            img = ImageOps.exif_transpose(img)  # phone photos store rotation in a tag
            rgb = np.array(img.convert("RGB"))
    except ProcessingError:
        raise
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError):
        raise ProcessingError("unreadable_document")
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def to_grayscale(image: np.ndarray) -> np.ndarray:
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def resize_for_ocr(gray: np.ndarray) -> np.ndarray:
    """Enlarge small images and shrink huge ones so text is a good size for OCR."""
    long_side = max(gray.shape)
    if long_side < TARGET_LONG_SIDE:
        scale = min(TARGET_LONG_SIDE / long_side, 3.0)
        return cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
    if long_side > MAX_LONG_SIDE:
        scale = MAX_LONG_SIDE / long_side
        return cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    return gray


def rotate_clockwise(gray: np.ndarray, degrees: int) -> np.ndarray:
    """Rotate by a multiple of 90 degrees (clockwise)."""
    codes = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return cv2.rotate(gray, codes[degrees]) if degrees in codes else gray


def _rotate_small_angle(gray: np.ndarray, angle: float) -> np.ndarray:
    height, width = gray.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    return cv2.warpAffine(
        gray, matrix, (width, height), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE
    )


def flatten_lighting(gray: np.ndarray) -> np.ndarray:
    """Even out shadows and uneven lighting.

    We estimate the paper's brightness everywhere (a "closing" erases the thin dark text,
    leaving only the background), then divide the image by it so the paper becomes
    uniformly white.
    """
    kernel_size = max(15, int(max(gray.shape) / 60)) | 1  # odd number
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    # Smooth first: the closing step takes local maximums, so raw noise would push the
    # background estimate too bright and the correction would fall short.
    smoothed = cv2.medianBlur(gray, 5)
    background = cv2.morphologyEx(smoothed, cv2.MORPH_CLOSE, kernel)
    background = cv2.GaussianBlur(background, (0, 0), sigmaX=kernel_size)
    return cv2.divide(gray, background, scale=255)


def estimate_skew_angle(gray: np.ndarray, max_angle: float = 12.0, step: float = 0.5) -> float:
    """Find the small tilt of the text lines, in degrees.

    Text lines are easiest to see when they are perfectly horizontal: the rows then
    alternate sharply between 'lots of ink' and 'blank'. We try small rotations and keep
    the one that makes that pattern sharpest.
    """
    scale = 800 / max(gray.shape)
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA) if scale < 1 else gray
    _, ink = cv2.threshold(flatten_lighting(small), 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    if cv2.countNonZero(ink) < 50:
        return 0.0

    best_angle, best_score = 0.0, -1.0
    for angle in np.arange(-max_angle, max_angle + step, step):
        rows = _rotate_small_angle(ink, float(angle)).sum(axis=1).astype(np.float64)
        score = float(np.var(rows))
        if score > best_score:
            best_angle, best_score = float(angle), score
    return best_angle


def deskew(gray: np.ndarray) -> np.ndarray:
    angle = estimate_skew_angle(gray)
    if abs(angle) < 0.3:
        return gray
    return _rotate_small_angle(gray, angle)


def clean_for_ocr(gray: np.ndarray) -> np.ndarray:
    """Stronger clean-up for poor photos: flattens lighting and removes noise.

    Used as a second attempt only when the first OCR pass is not confident, because on
    already-clean scans it adds nothing. We deliberately do NOT hard-threshold to black and
    white here: on noisy photos that creates speckle that slows OCR and hurts accuracy.
    """
    return cv2.bilateralFilter(flatten_lighting(gray), 9, 50, 50)
