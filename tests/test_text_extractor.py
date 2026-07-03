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
    text = extractor.clean_text("Chapter one. 42 Next page starts here.")
    assert "42" not in text
    assert "Chapter one" in text


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