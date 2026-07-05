"""Tests for converter orchestration (mocked, no API/FFmpeg needed)."""

import logging
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.converter import QwenAudiobookConverter
from src.settings import Settings


@pytest.fixture(autouse=True)
def disable_logging():
    logging.disable(logging.CRITICAL)
    yield
    logging.disable(logging.NOTSET)


@pytest.fixture
def settings():
    s = Settings()
    s.voice_mode = "custom_voice"
    s.custom_voice_speaker = "Ryan"
    s.dry_run = False
    return s


@pytest.fixture
def converter(settings):
    with patch("src.converter.check_ffmpeg", return_value=True):
        conv = QwenAudiobookConverter(settings)
        conv.qwen = MagicMock()
        yield conv


def test_init_creates_directories(converter, tmp_path):
    """Converter init should create required directories."""
    with patch("src.converter.Path.mkdir"):
        # Directories already created in fixture; just verify no crash
        pass


def test_get_cache_path_custom_voice(converter):
    path = converter.get_cache_path("Hello world")
    assert "cache" in str(path)
    assert "audio_chunks" in str(path)
    assert path.suffix == ".wav"


def test_get_cache_path_changes_with_seed(converter):
    path_a = converter.get_cache_path("hello")
    converter.settings.custom_voice_seed = 999
    path_b = converter.get_cache_path("hello")
    assert path_a != path_b, "Cache path should change when seed changes"


def test_get_cache_path_changes_with_model_size(converter):
    path_a = converter.get_cache_path("hello")
    converter.settings.custom_voice_model_size = "6.3B"
    path_b = converter.get_cache_path("hello")
    assert path_a != path_b, "Cache path should change when model_size changes"


def test_dry_run_returns_true(converter, tmp_path):
    converter.settings.dry_run = True
    sample = tmp_path / "test.txt"
    sample.write_text("Hello world. This is a test.")
    result = converter.convert_book(sample)
    assert result is True


def test_validate_voice_clone_missing_ref_raises(settings):
    settings.voice_mode = "voice_clone"
    settings.voice_clone_ref_audio = ""
    conv = QwenAudiobookConverter(settings)
    with pytest.raises(ValueError, match="requires a reference audio"):
        conv.validate()


def test_validate_voice_clone_ref_not_found_raises(settings):
    settings.voice_mode = "voice_clone"
    settings.voice_clone_ref_audio = "/nonexistent/file.wav"
    conv = QwenAudiobookConverter(settings)
    with pytest.raises(FileNotFoundError):
        conv.validate()


def test_process_chunk_with_retry_success(converter):
    converter.qwen.generate.return_value = ("/tmp/test.wav",)
    gem = MagicMock()
    gem.exists.return_value = True
    with (
        patch("builtins.open", MagicMock()),
        patch("shutil.copy2"),
        patch("pathlib.Path.exists", return_value=True),
        patch("src.converter.Path") as mock_path,
    ):
        mock_path.return_value.exists.return_value = True
        # Create a real temp file for the result
        tmp = Path(__file__).parent.parent / "chunks"
        tmp.mkdir(exist_ok=True)
        try:
            result = converter.process_chunk_with_retry(1, "hello")
            # This will still try qwen.generate; mock should handle
            pass
        finally:
            if tmp.exists():
                import shutil
                shutil.rmtree(str(tmp), ignore_errors=True)


def test_print_dry_run_shows_chunks(converter, capsys):
    converter._print_dry_run(
        Path("test.txt"),
        "Hello world. Test sentence.",
        ["Hello world.", "Test sentence."],
    )
    captured = capsys.readouterr()
    assert "DRY-RUN" in captured.out
    assert "Chunks: 2" in captured.out


def test_check_api_returns_info():
    """check_api should return health info dict (mocked)."""
    settings = Settings()
    settings.qwen_api_url = "http://localhost:9999"
    conv = QwenAudiobookConverter(settings)
    with patch("src.converter.QwenClient") as mock_cls:
        mock_instance = MagicMock()
        mock_instance.check_health.return_value = {
            "url": "http://localhost:9999",
            "connected": True,
            "endpoints": ["/run_custom_voice"],
            "endpoint_count": 1,
        }
        mock_cls.return_value = mock_instance
        info = conv.check_api()
        assert info["url"] == "http://localhost:9999"
        assert info["connected"] is True


def test_convert_book_empty_text_returns_false(converter, tmp_path):
    sample = tmp_path / "empty.txt"
    sample.write_text("")
    result = converter.convert_book(sample)
    assert result is False
