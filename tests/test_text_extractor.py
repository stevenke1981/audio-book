"""Tests for text extraction."""

from pathlib import Path

import pytest

from src.text_extractor import TextExtractor


@pytest.fixture
def extractor():
    return TextExtractor(clean_page_numbers=True, normalize_whitespace=True)


def test_clean_html_strips_tags(extractor):
    html = "<html><body><p>Hello <b>world</b></p><script>bad()</script></body></html>"
    text = extractor.clean_html(html)
    assert "Hello" in text
    assert "world" in text
    assert "bad" not in text
    assert "<" not in text


def test_clean_text_removes_page_numbers(extractor):
    # Line-isolated page number (\n42\n) should be removed
    text = extractor.clean_text("Chapter one.\n42\nNext page starts here.")
    assert "42" not in text
    assert "Chapter one" in text
    assert "Next page starts" in text


def test_clean_text_preserves_inline_numbers(extractor):
    # Numbers inline with text (not line-isolated) should be preserved
    text = extractor.clean_text("Chapter one. 42 Next page starts here.")
    assert "42" in text


def test_clean_text_normalizes_whitespace(extractor):
    text = extractor.clean_text("Hello    world\n\n\ttest")
    assert text == "Hello world test"


def test_extract_txt_utf8(extractor, tmp_path):
    f = tmp_path / "test.txt"
    f.write_text("你好 Hello 世界", encoding="utf-8")
    text = extractor.extract(f)
    assert "Hello" in text
    assert "你好" in text


def test_extract_unsupported_format(extractor, tmp_path):
    f = tmp_path / "test.xyz"
    f.write_text("data")
    with pytest.raises(ValueError, match="Unsupported"):
        extractor.extract(f)


# --- Phase 7: page number false-positive fixes (EXT-05/06) ---

def test_clean_text_preserves_chapter_numbers(extractor):
    """Chapter numbers like 'Chapter 42' should not be removed."""
    text = extractor.clean_text("Chapter 42 The Great Adventure")
    assert "42" in text
    assert "Chapter 42" in text


def test_clean_text_preserves_years(extractor):
    """Years like '2025' should not be removed as page numbers."""
    text = extractor.clean_text("In 2025 the story begins")
    assert "2025" in text


def test_clean_text_removes_isolated_page_number(extractor):
    """Line-isolated page numbers (e.g. at start on a line) should be removed."""
    text = extractor.clean_text("some text\n42\nmore text")
    # With new regex, \n42\n should match
    # After normalize_whitespace, the \n become spaces
    # So we check the result
    assert " 42 " not in text or text.find("42") == -1


def test_clean_text_without_page_number_flag(extractor):
    """When clean_page_numbers=False, all numbers should be preserved."""
    ex = TextExtractor(clean_page_numbers=False, normalize_whitespace=True)
    text = ex.clean_text("Page 42 of text 2025")
    assert "42" in text
    assert "2025" in text