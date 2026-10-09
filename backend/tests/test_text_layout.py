from app.services.text_layout import LayoutWord, words_to_lines


def word(text, x0, y0, width=40, height=10):
    return LayoutWord(x0, y0, x0 + width, y0 + height, text)


def test_table_cells_become_one_row_with_column_gaps():
    words = [
        word("12.0", 300, 100), word("Hemoglobin", 50, 100), word("10.2", 150, 101), word("g/dL", 230, 99),
    ]
    assert words_to_lines(words) == ["Hemoglobin  10.2  g/dL  12.0"]


def test_close_words_are_joined_with_single_spaces():
    words = [word("12.0", 50, 100, width=30), word("-", 85, 100, width=5), word("16.0", 95, 100, width=30)]
    assert words_to_lines(words) == ["12.0 - 16.0"]


def test_different_heights_make_separate_lines_in_reading_order():
    words = [word("second", 50, 140), word("first", 50, 100)]
    assert words_to_lines(words) == ["first", "second"]


def test_empty_input_gives_no_lines():
    assert words_to_lines([]) == []
    assert words_to_lines([word("   ", 0, 0)]) == []
