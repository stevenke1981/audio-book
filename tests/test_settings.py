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


# --- Phase 7: settings_hash completeness (SET-05~07) ---

def test_settings_hash_changes_with_model_size():
    s1 = Settings(custom_voice_model_size="1.7B")
    s2 = Settings(custom_voice_model_size="6.3B")
    assert s1.settings_hash() != s2.settings_hash()


def test_settings_hash_changes_with_seed():
    s1 = Settings(custom_voice_seed=42)
    s2 = Settings(custom_voice_seed=99)
    assert s1.settings_hash() != s2.settings_hash()


def test_settings_hash_changes_with_audio_bitrate():
    s1 = Settings(audio_bitrate="128k")
    s2 = Settings(audio_bitrate="192k")
    assert s1.settings_hash() != s2.settings_hash()


def test_settings_hash_changes_with_voice_clone_language():
    s1 = Settings(voice_clone_language="English")
    s2 = Settings(voice_clone_language="Chinese")
    assert s1.settings_hash() != s2.settings_hash()


def test_settings_hash_changes_with_voice_design_seed():
    s1 = Settings(voice_design_seed=0)
    s2 = Settings(voice_design_seed=100)
    assert s1.settings_hash() != s2.settings_hash()