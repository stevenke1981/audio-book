"""Tests for QwenClient (mocked, no Gradio API needed)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.qwen_client import QwenClient
from src.settings import Settings


@pytest.fixture
def mock_client():
    """Create a QwenClient with mocked gradio_client.Client."""
    with patch("src.qwen_client.Client") as mock_cls:
        instance = MagicMock()
        instance.view_api.return_value = {
            "named_endpoints": {
                "/run_custom_voice": {"parameters": []},
                "/generate_voice_design": {"parameters": []},
                "/generate_voice_clone": {"parameters": []},
                "/transcribe_audio": {"parameters": []},
            }
        }
        mock_cls.return_value = instance
        settings = Settings()
        client = QwenClient(settings)
        client.client = instance
        client.api_info = instance.view_api()
        yield client


def test_resolve_api_name_found(mock_client):
    name = mock_client._resolve_api_name("/run_custom_voice", "/generate_custom_voice")
    assert name == "/run_custom_voice"


def test_resolve_api_name_fallback(mock_client):
    name = mock_client._resolve_api_name(
        "/nonexistent", "/generate_custom_voice", "/run_custom_voice"
    )
    # Should skip /nonexistent, find /generate_custom_voice
    assert name in mock_client.api_info["named_endpoints"]


def test_resolve_api_name_raises_on_no_match(mock_client):
    with pytest.raises(ValueError, match="None of the expected API endpoints"):
        mock_client._resolve_api_name("/not_there", "/also_missing")


def test_generate_dispatches_custom_voice(mock_client):
    mock_client.client.predict.return_value = ("/tmp/audio.wav",)
    result = mock_client.generate("Hello", "custom_voice")
    assert result is not None


def test_generate_dispatches_voice_design(mock_client):
    mock_client.client.predict.return_value = ("/tmp/audio.wav",)
    result = mock_client.generate("Hello", "voice_design")
    assert result is not None


def test_generate_raises_on_unknown_mode(mock_client):
    with pytest.raises(ValueError, match="Unknown voice mode"):
        mock_client.generate("Hello", "invalid_mode")


def test_voice_clone_endpoint_resolution(mock_client):
    """Voice clone should use _resolve_api_name, not hardcoded string."""
    clone_api = mock_client._resolve_api_name(
        "/generate_voice_clone", "/run_voice_clone"
    )
    assert clone_api == "/generate_voice_clone"


def test_check_health_returns_endpoints(mock_client):
    health = mock_client.check_health()
    assert health["connected"] is True
    assert health["endpoint_count"] >= 3


def test_list_endpoints(mock_client):
    endpoints = mock_client.list_endpoints()
    assert "/run_custom_voice" in endpoints
    assert "/generate_voice_clone" in endpoints
