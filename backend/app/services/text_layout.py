"""Rebuilds readable text lines from words that have positions on the page.

Lab reports are tables. Reading a PDF word by word can put each table cell on its own line
("Hemoglobin", "10.2", "g/dL"). Grouping words by their vertical position puts a whole row
back together ("Hemoglobin  10.2  g/dL  12.0 - 16.0"). Two spaces mark a wide gap, which
usually means a new table column.
"""
from dataclasses import dataclass

COLUMN_GAP_FACTOR = 1.5  # a gap wider than 1.5 x the text height counts as a column break


@dataclass(frozen=True)
class LayoutWord:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str


def join_line(words: list[LayoutWord], line_height: float) -> str:
    """Join one row of words left-to-right, using two spaces at wide gaps."""
    ordered = sorted(words, key=lambda word: word.x0)
    parts = [ordered[0].text]
    for previous, current in zip(ordered, ordered[1:]):
        wide_gap = (current.x0 - previous.x1) >= COLUMN_GAP_FACTOR * line_height
        parts.append("  " if wide_gap else " ")
        parts.append(current.text)
    return "".join(parts)


def words_to_lines(words: list[LayoutWord]) -> list[str]:
    items = [word for word in words if word.text.strip()]
    if not items:
        return []

    heights = sorted(word.y1 - word.y0 for word in items)
    median_height = heights[len(heights) // 2] or 1.0

    items.sort(key=lambda word: (word.y0 + word.y1) / 2)
    rows: list[list[LayoutWord]] = [[items[0]]]
    row_center = (items[0].y0 + items[0].y1) / 2
    for word in items[1:]:
        center = (word.y0 + word.y1) / 2
        if abs(center - row_center) <= 0.5 * median_height:
            rows[-1].append(word)
            row_center = sum((w.y0 + w.y1) / 2 for w in rows[-1]) / len(rows[-1])
        else:
            rows.append([word])
            row_center = center

    return [join_line(row, median_height) for row in rows]
