"""Qwen Gradio API client wrapper."""

from __future__ import annotations

import io
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from gradio_client import Client, handle_file

from .settings import Settings

logger = logging.getLogger(__name__)


class QwenClient:
    """Wrapper around Qwen3 TTS Gradio API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[Client] = None
        self.api_info: Dict[str, Any] = {}
        self.voice_clone_ref_text: str = settings.voice_clone_ref_text

    def connect(self) -> None:
        logger.info("Connecting to Qwen API at %s...", self.settings.qwen_api_url)
        old_stdout = sys.stdout
        sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8", errors="replace")
        try:
            self.client = Client(self.settings.qwen_api_url)
        finally:
            sys.stdout = old_stdout
        self.api_info = self._load_api_info()
        logger.info("Connected to Qwen API")

    def check_health(self) -> Dict[str, Any]:
        """Return API health info without full conversion setup."""
        self.connect()
        endpoints = list(self.api_info.get("named_endpoints", {}).keys())
        return {
            "url": self.settings.qwen_api_url,
            "connected": True,
            "endpoints": endpoints,
            "endpoint_count": len(endpoints),
        }

    def transcribe(self, audio_path: str) -> str:
        if self.client is None:
            raise RuntimeError("Client not connected")
        transcribe_api = self._resolve_api_name("/transcribe_audio", "/run_transcribe_audio")
        logger.info("Transcribing audio: %s", audio_path)
        result = self.client.predict(
            audio=handle_file(audio_path),
            api_name=transcribe_api,
        )
        text = result if isinstance(result, str) else str(result)
        logger.info("Transcription complete: %s...", text[:100])
        return text.strip()

    def prepare_voice_clone(self, ref_audio: str) -> str:
        self.voice_clone_ref_text = self.transcribe(ref_audio)
        return self.voice_clone_ref_text

    def generate(self, text: str, voice_mode: str) -> Tuple[Any, ...]:
        if voice_mode == "custom_voice":
            return self._generate_custom_voice(text)
        if voice_mode == "voice_clone":
            return self._generate_voice_clone(text)
        if voice_mode == "voice_design":
            return self._generate_voice_design(text)
        raise ValueError(f"Unknown voice mode: {voice_mode}")

    def _generate_custom_voice(self, text: str) -> Tuple:
        custom_api = self._resolve_api_name("/run_custom_voice", "/generate_custom_voice")
        payload = dict(
            text=text,
            language=self.settings.custom_voice_language,
            speaker=self.settings.custom_voice_speaker,
            instruct=self.settings.custom_voice_instruct,
        )
        if self._endpoint_accepts_param(custom_api, "model_id_cv"):
            payload["model_id_cv"] = self.settings.custom_voice_model_id
        elif self._endpoint_accepts_param(custom_api, "model_size"):
            payload["model_size"] = self.settings.custom_voice_model_size
        if self._endpoint_accepts_param(custom_api, "seed"):
            payload["seed"] = self.settings.custom_voice_seed
        return self.client.predict(**payload, api_name=custom_api)

    def _generate_voice_clone(self, text: str) -> Tuple:
        ref_audio = self.settings.voice_clone_ref_audio
        if not Path(ref_audio).exists():
            raise FileNotFoundError(f"Reference audio not found: {ref_audio}")
        if not self.voice_clone_ref_text:
            raise ValueError("Reference text is required for voice cloning")
        clone_api = self._resolve_api_name(
            "/generate_voice_clone", "/run_voice_clone"
        )
        return self.client.predict(
            ref_audio=handle_file(ref_audio),
            ref_text=self.voice_clone_ref_text,
            target_text=text,
            language=self.settings.voice_clone_language,
            use_xvector_only=self.settings.voice_clone_use_xvector_only,
            model_size=self.settings.voice_clone_model_size,
            max_chunk_chars=self.settings.voice_clone_max_chunk_chars,
            chunk_gap=self.settings.voice_clone_chunk_gap,
            seed=self.settings.voice_clone_seed,
            api_name=clone_api,
        )

    def _generate_voice_design(self, text: str) -> Tuple:
        design_api = self._resolve_api_name(
            "/generate_voice_design", "/run_voice_design"
        )
        payload = dict(
            text=text,
            language=self.settings.voice_design_language,
            description=self.settings.voice_design_description,
        )
        if self._endpoint_accepts_param(design_api, "seed"):
            payload["seed"] = self.settings.voice_design_seed
        return self.client.predict(**payload, api_name=design_api)

    def _load_api_info(self) -> Dict[str, Any]:
        try:
            return self.client.view_api(return_format="dict")
        except Exception as exc:
            logger.warning("Unable to read API metadata: %s", exc)
            return {}

    def _resolve_api_name(self, *candidates: str) -> str:
        named_endpoints = self.api_info.get("named_endpoints", {})
        for candidate in candidates:
            if candidate in named_endpoints:
                return candidate
        raise ValueError(
            f"None of the expected API endpoints found: {candidates}. "
            f"Available endpoints: {list(named_endpoints.keys())}"
        )

    def _endpoint_accepts_param(self, api_name: str, param_name: str) -> bool:
        endpoint = self.api_info.get("named_endpoints", {}).get(api_name, {})
        parameters = endpoint.get("parameters", [])
        return any(p.get("parameter_name") == param_name for p in parameters)

    def list_endpoints(self) -> List[str]:
        return list(self.api_info.get("named_endpoints", {}).keys())