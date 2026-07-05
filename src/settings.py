"""Settings loading from config.py, YAML, environment, and CLI."""

from __future__ import annotations

import hashlib
import importlib
import os
from dataclasses import dataclass, field, fields
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    yaml = None


@dataclass
class Settings:
    qwen_api_url: str = "http://127.0.0.1:7860"
    api_timeout: int = 300
    max_retries: int = 3

    voice_mode: str = "custom_voice"

    custom_voice_speaker: str = "Ryan"
    custom_voice_language: str = "English"
    custom_voice_instruct: str = (
        "Speak naturally and clearly, as if reading a dramatic book to an adult audience."
    )
    custom_voice_model_size: str = "1.7B"
    custom_voice_seed: int = -1
    custom_voice_model_id: str = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"

    voice_clone_ref_audio: str = ""
    voice_clone_ref_text: str = ""
    voice_clone_language: str = "English"
    voice_clone_use_xvector_only: bool = False
    voice_clone_model_size: str = "1.7B"
    voice_clone_max_chunk_chars: int = 200
    voice_clone_chunk_gap: int = 0
    voice_clone_seed: int = -1

    voice_design_language: str = "English"
    voice_design_description: str = (
        "Speak in a clear, professional narrator voice suitable for reading audiobooks."
    )
    voice_design_seed: int = -1

    books_folder: str = "book_to_convert"
    audiobooks_folder: str = "audiobooks"
    chunk_size_words: int = 1500
    max_workers: int = 1
    min_delay_between_chunks: int = 1

    audio_format: str = "mp3"
    audio_bitrate: str = "128k"

    supported_formats: List[str] = field(
        default_factory=lambda: [".txt", ".pdf", ".epub", ".docx", ".doc"]
    )
    clean_page_numbers: bool = True
    normalize_whitespace: bool = True
    sentence_boundary_detection: bool = True

    enable_caching: bool = True
    cache_cleanup_days: int = 30

    log_level: str = "INFO"
    log_to_file: bool = True
    log_to_console: bool = True

    dry_run: bool = False
    resume: bool = False
    force_restart: bool = False
    no_cache: bool = False

    def settings_hash(self) -> str:
        """Hash voice-related settings for resume validation."""
        parts = [
            self.voice_mode,
            # Custom Voice
            self.custom_voice_speaker,
            self.custom_voice_language,
            self.custom_voice_instruct,
            self.custom_voice_model_size,
            self.custom_voice_model_id,
            str(self.custom_voice_seed),
            # Voice Clone
            self.voice_clone_ref_audio,
            self.voice_clone_language,
            self.voice_clone_model_size,
            str(self.voice_clone_use_xvector_only),
            str(self.voice_clone_seed),
            # Voice Design
            self.voice_design_language,
            self.voice_design_description,
            str(self.voice_design_seed),
            # Output
            self.audio_format,
            self.audio_bitrate,
            str(self.chunk_size_words),
        ]
        return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

    def apply_overrides(self, overrides: Dict[str, Any]) -> "Settings":
        valid = {f.name for f in fields(self)}
        data = {f.name: getattr(self, f.name) for f in fields(self)}
        for key, value in overrides.items():
            if key in valid and value is not None:
                data[key] = value
        return Settings(**data)


def _load_config_module() -> Dict[str, Any]:
    try:
        config = importlib.import_module("config")
    except ImportError:
        return {}
    mapping = {
        "qwen_api_url": "QWEN_API_URL",
        "api_timeout": "API_TIMEOUT",
        "max_retries": "MAX_RETRIES",
        "voice_mode": "VOICE_MODE",
        "custom_voice_speaker": "CUSTOM_VOICE_SPEAKER",
        "custom_voice_language": "CUSTOM_VOICE_LANGUAGE",
        "custom_voice_instruct": "CUSTOM_VOICE_INSTRUCT",
        "custom_voice_model_size": "CUSTOM_VOICE_MODEL_SIZE",
        "custom_voice_seed": "CUSTOM_VOICE_SEED",
        "custom_voice_model_id": "CUSTOM_VOICE_MODEL_ID",
        "voice_clone_ref_audio": "VOICE_CLONE_REF_AUDIO",
        "voice_clone_ref_text": "VOICE_CLONE_REF_TEXT",
        "voice_clone_language": "VOICE_CLONE_LANGUAGE",
        "voice_clone_use_xvector_only": "VOICE_CLONE_USE_XVECTOR_ONLY",
        "voice_clone_model_size": "VOICE_CLONE_MODEL_SIZE",
        "voice_clone_max_chunk_chars": "VOICE_CLONE_MAX_CHUNK_CHARS",
        "voice_clone_chunk_gap": "VOICE_CLONE_CHUNK_GAP",
        "voice_clone_seed": "VOICE_CLONE_SEED",
        "voice_design_language": "VOICE_DESIGN_LANGUAGE",
        "voice_design_description": "VOICE_DESIGN_DESCRIPTION",
        "voice_design_seed": "VOICE_DESIGN_SEED",
        "books_folder": "BOOKS_FOLDER",
        "audiobooks_folder": "AUDIOBOOKS_FOLDER",
        "chunk_size_words": "CHUNK_SIZE_WORDS",
        "max_workers": "MAX_WORKERS",
        "min_delay_between_chunks": "MIN_DELAY_BETWEEN_CHUNKS",
        "audio_format": "AUDIO_FORMAT",
        "audio_bitrate": "AUDIO_BITRATE",
        "supported_formats": "SUPPORTED_FORMATS",
        "clean_page_numbers": "CLEAN_PAGE_NUMBERS",
        "normalize_whitespace": "NORMALIZE_WHITESPACE",
        "sentence_boundary_detection": "SENTENCE_BOUNDARY_DETECTION",
        "enable_caching": "ENABLE_CACHING",
        "cache_cleanup_days": "CACHE_CLEANUP_DAYS",
        "log_level": "LOG_LEVEL",
        "log_to_file": "LOG_TO_FILE",
        "log_to_console": "LOG_TO_CONSOLE",
    }
    result: Dict[str, Any] = {}
    for key, attr in mapping.items():
        if hasattr(config, attr):
            result[key] = getattr(config, attr)
    return result


def _load_yaml(path: Path) -> Dict[str, Any]:
    if yaml is None:
        raise ImportError("PyYAML is required for --config. pip install PyYAML")
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return {k: v for k, v in data.items() if v is not None}


def _load_env() -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if url := os.environ.get("QWEN_API_URL"):
        result["qwen_api_url"] = url
    if inp := os.environ.get("AUDIOBOOK_INPUT_DIR"):
        result["books_folder"] = inp
    if out := os.environ.get("AUDIOBOOK_OUTPUT_DIR"):
        result["audiobooks_folder"] = out
    return result


def load_settings(
    config_path: Optional[str] = None,
    cli_overrides: Optional[Dict[str, Any]] = None,
) -> Settings:
    """Load settings: defaults < config.py < YAML < env < CLI."""
    settings = Settings()
    settings = settings.apply_overrides(_load_config_module())
    if config_path:
        settings = settings.apply_overrides(_load_yaml(Path(config_path)))
    settings = settings.apply_overrides(_load_env())
    if cli_overrides:
        settings = settings.apply_overrides(cli_overrides)
    return settings