"""Builds fake test documents in code, so no medical files or binaries live in the repo.

All names and values are invented. Spaces of 2+ characters separate table columns.
"""
import io
import re

import cv2
import numpy as np
import pymupdf
from PIL import Image, ImageDraw, ImageFont

LAB_REPORT_LINES = [
    "CITY MEDICAL LABORATORY",
    "Patient: Test Patient    Collected: 12/01/2026",
    "",
    "Test    Result    Unit    Reference Range",
    "Hemoglobin    10.2    g/dL    12.0 - 16.0",
    "WBC Count    7400    /uL    4000 - 11000",
    "Glucose    92    mg/dL    70 - 99",
    "Platelets    250    10^3/uL    150 - 450",
]

# Words that must be found for us to say "the report was read correctly"
EXPECTED_WORDS = ["Hemoglobin", "10.2", "12.0", "WBC", "7400", "Glucose", "Platelets"]


def words_found(text: str) -> int:
    return sum(word in text for word in EXPECTED_WORDS)


# ---------------- PDFs ----------------
def make_digital_pdf(lines: list[str] = LAB_REPORT_LINES) -> bytes:
    """A PDF with real embedded text; each table cell is placed separately, like real lab PDFs."""
    doc = pymupdf.open()
    page = doc.new_page()
    y = 72
    for line in lines:
        for column, cell in enumerate(re.split(r"\s{2,}", line)):
            if cell:
                page.insert_text((72 + column * 120, y), cell, fontsize=11)
        y += 20
    return doc.tobytes()


def make_scanned_pdf(image: np.ndarray) -> bytes:
    """A PDF whose only content is a picture, with no embedded text."""
    height, width = image.shape[:2]
    doc = pymupdf.open()
    page = doc.new_page(width=595, height=595 * height / width)
    page.insert_image(page.rect, stream=to_png_bytes(image))
    return doc.tobytes()


def make_blank_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page()
    return doc.tobytes()


def make_pdf_with_pages(page_count: int) -> bytes:
    doc = pymupdf.open()
    for number in range(page_count):
        doc.new_page().insert_text((72, 72), f"Page {number + 1} " + "text " * 40, fontsize=11)
    return doc.tobytes()


def make_password_protected_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "secret " * 40)
    return doc.tobytes(
        encryption=pymupdf.PDF_ENCRYPT_AES_256, owner_pw="owner-secret", user_pw="user-secret"
    )


# ---------------- images ----------------
def render_report(lines: list[str] = LAB_REPORT_LINES, font_size: int = 26) -> np.ndarray:
    """Draw a report as a clean grayscale image (like a good scan)."""
    font = ImageFont.load_default(size=font_size)
    image = Image.new("L", (1300, 120 + 48 * len(lines)), 255)
    draw = ImageDraw.Draw(image)
    for row, line in enumerate(lines):
        draw.text((40, 40 + row * 48), line, font=font, fill=20)
    return np.array(image)


def rotate_small(image: np.ndarray, degrees: float) -> np.ndarray:
    height, width = image.shape
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), degrees, 1.0)
    return cv2.warpAffine(image, matrix, (width, height), borderValue=255)


def rotate_quarter(image: np.ndarray, degrees_clockwise: int) -> np.ndarray:
    codes = {90: cv2.ROTATE_90_CLOCKWISE, 180: cv2.ROTATE_180, 270: cv2.ROTATE_90_COUNTERCLOCKWISE}
    return cv2.rotate(image, codes[degrees_clockwise])


def blur(image: np.ndarray, sigma: float) -> np.ndarray:
    return cv2.GaussianBlur(image, (0, 0), sigma)


def add_noise(image: np.ndarray, strength: float = 40) -> np.ndarray:
    noise = np.random.RandomState(0).normal(0, strength, image.shape)
    return np.clip(image.astype(float) + noise, 0, 255).astype(np.uint8)


def add_uneven_lighting(image: np.ndarray, darkest: float = 0.5) -> np.ndarray:
    gradient = np.linspace(darkest, 1.0, image.shape[1])[None, :]
    noise = np.random.RandomState(0).normal(0, 15, image.shape)
    return np.clip(image * gradient + noise, 0, 255).astype(np.uint8)


def to_png_bytes(image: np.ndarray) -> bytes:
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def to_jpeg_bytes(image: np.ndarray, exif_orientation: int | None = None) -> bytes:
    buffer = io.BytesIO()
    pil_image = Image.fromarray(image)
    if exif_orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = exif_orientation
        pil_image.save(buffer, "JPEG", exif=exif)
    else:
        pil_image.save(buffer, "JPEG")
    return buffer.getvalue()
