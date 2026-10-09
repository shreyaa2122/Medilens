"""Reads text from images with Tesseract.

Strategy for each image:
  1. Light clean-up (grayscale, resize, fix rotation, straighten) and read it.
  2. If Tesseract is not confident, try a stronger clean-up (even out lighting, remove
     noise) and keep whichever attempt read more text with confidence.

Confidence is the average per-word confidence reported by Tesseract. It describes how
sure the OCR engine is about the characters it read. It is NOT medical certainty.
"""
import threading
from dataclasses import dataclass

import numpy as np
import pytesseract
from pytesseract import Output

from app.services.image_preprocessing import (
    clean_for_ocr,
    deskew,
    resize_for_ocr,
    rotate_clockwise,
    to_grayscale,
)
from app.services.processing_errors import ProcessingError
from app.services.text_layout import LayoutWord, join_line

GOOD_ENOUGH_CONFIDENCE = 0.80      # above this, skip the second attempt
CONFIDENT_WORD_THRESHOLD = 0.60    # a word counts as "confidently read" above this
MIN_ORIENTATION_CONFIDENCE = 1.0   # Tesseract's own scale; below this we don't rotate


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float          # 0.0 - 1.0, mean per-word confidence
    confident_characters: int  # characters in confidently-read words (used to compare attempts)
    word_count: int


EMPTY_RESULT = OcrResult(text="", confidence=0.0, confident_characters=0, word_count=0)


class OcrService:
    def __init__(self, tesseract_cmd: str = "", language: str = "eng", timeout_seconds: int = 60):
        self.tesseract_cmd = tesseract_cmd or "tesseract"
        self.language = language
        self.timeout_seconds = timeout_seconds
        # Tesseract already uses the CPU heavily. Running several images at once is not
        # faster and uses much more memory, so documents are read one at a time.
        self._one_at_a_time = threading.Lock()

    def _select_engine(self) -> None:
        # pytesseract keeps the executable path in one global variable, so each call
        # sets it first. This keeps separate OcrService objects from affecting each other.
        pytesseract.pytesseract.tesseract_cmd = self.tesseract_cmd

    def is_available(self) -> bool:
        self._select_engine()
        try:
            pytesseract.get_tesseract_version()
            return True
        except (pytesseract.TesseractNotFoundError, OSError):
            return False

    def read_image(self, image: np.ndarray) -> OcrResult:
        with self._one_at_a_time:
            return self._read_image(image)

    def _read_image(self, image: np.ndarray) -> OcrResult:
        gray = resize_for_ocr(to_grayscale(image))
        gray = self._fix_orientation(gray)
        gray = deskew(gray)

        first_attempt = self._recognize(gray)
        if first_attempt.confidence >= GOOD_ENOUGH_CONFIDENCE:
            return first_attempt

        second_attempt = self._recognize(clean_for_ocr(gray))
        if second_attempt.confident_characters > first_attempt.confident_characters:
            return second_attempt
        return first_attempt

    def _fix_orientation(self, gray: np.ndarray) -> np.ndarray:
        """Turn sideways or upside-down pages upright using Tesseract's orientation detection."""
        self._select_engine()
        try:
            info = pytesseract.image_to_osd(
                gray, config="--psm 0", output_type=Output.DICT, timeout=self.timeout_seconds
            )
        except pytesseract.TesseractNotFoundError:
            raise ProcessingError("ocr_unavailable")
        except Exception:
            return gray  # too little text to judge, or orientation data missing: leave as is

        clockwise_turn = int(info.get("rotate", 0))
        confidence = float(info.get("orientation_conf", 0))
        if clockwise_turn in (90, 180, 270) and confidence >= MIN_ORIENTATION_CONFIDENCE:
            return rotate_clockwise(gray, clockwise_turn)
        return gray

    def _recognize(self, gray: np.ndarray) -> OcrResult:
        self._select_engine()
        try:
            data = pytesseract.image_to_data(
                gray,
                lang=self.language,
                config="--psm 6",  # one uniform block: keeps table rows together
                output_type=Output.DICT,
                timeout=self.timeout_seconds,
            )
        except pytesseract.TesseractNotFoundError:
            raise ProcessingError("ocr_unavailable")
        except (pytesseract.TesseractError, RuntimeError):
            raise ProcessingError("ocr_failed")
        return _build_result(data)


def _build_result(data: dict) -> OcrResult:
    lines: dict[tuple[int, int, int], list[LayoutWord]] = {}
    confidences: list[float] = []
    confident_characters = 0

    for index, text in enumerate(data["text"]):
        text = text.strip()
        confidence = float(data["conf"][index])
        if not text or confidence < 0:
            continue

        left, top = int(data["left"][index]), int(data["top"][index])
        width, height = int(data["width"][index]), int(data["height"][index])
        key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
        lines.setdefault(key, []).append(LayoutWord(left, top, left + width, top + height, text))

        confidences.append(confidence / 100)
        if confidence / 100 >= CONFIDENT_WORD_THRESHOLD:
            confident_characters += len(text)

    if not confidences:
        return EMPTY_RESULT

    rendered_lines = []
    for words in lines.values():
        line_height = sorted(w.y1 - w.y0 for w in words)[len(words) // 2] or 1
        rendered_lines.append(join_line(words, line_height))

    return OcrResult(
        text="\n".join(rendered_lines),
        confidence=float(np.mean(confidences)),
        confident_characters=confident_characters,
        word_count=len(confidences),
    )
