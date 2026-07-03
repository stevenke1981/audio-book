"""Tests for settings loading."""

import os

from src.settings import Settings, load_settings


def test_default_settings():
    s = Settings()
    assert s.custom_voice_speaker == "Ryan"
    assert s.audio_format == "mp3"
    assert s.chunk_size_words == 1500


def test_settings_hash_stable():
    s1 = Settings()
    s2 = Settings()
    assert s1.settings_hash() == s2.settings_hash()


def test_settings_hash_changes_with_speaker():
    s1 = Settings(custom_voice_speaker="Ryan")
    s2 = Settings(custom_voice_speaker="Serena")
    assert s1.settings_hash() != s2.settings_hash()


def test_cli_override_speaker():
    s = load_settings(cli_overrides={"custom_voice_speaker": "Serena"})
    assert s.custom_voice_speaker == "Serena"


def test_env_override_api_url(monkeypatch):
    monkeypatch.setenv("QWEN_API_URL", "http://localhost:9999")
    s = load_settings()
    assert s.qwen_api_url == "http://localhost:9999"