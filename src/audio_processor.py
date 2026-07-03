"""Audio chunk combination and export."""

from __future__ import annotations

import logging
import shutil
from pathlib import Path
from typing import Dict, Optional

from pydub import AudioSegment

from .settings import Settings

logger = logging.getLogger(__name__)


def check_ffmpeg() -> bool:
    """Check if ffmpeg is available for pydub."""
    from pydub.utils import which

    return which("ffmpeg") is not None


class AudioProcessor:
    """Combine WAV chunks and export to target format."""

    def __init__(self, settings: Settings, chunks_dir: Path = Path("chunks")):
        self.settings = settings
        self.chunks_dir = chunks_dir

    def combine_chunks(
        self,
        total_chunks: int,
        output_path: Path,
        results: Optional[Dict[int, bool]] = None,
    ) -> bool:
        try:
            combined = AudioSegment.empty()
            successful = 0
            missing_chunks = []

            for i in range(1, total_chunks + 1):
                if results is not None and not results.get(i, False):
                    missing_chunks.append(i)
                    continue

                chunk_file = self.chunks_dir / f"chunk_{i:04d}.wav"
                if chunk_file.exists():
                    try:
                        chunk_audio = AudioSegment.from_wav(str(chunk_file))
                        combined += chunk_audio
                        successful += 1
                        if successful % 10 == 0:
                            logger.info("Combined %d chunks", successful)
                    except Exception as exc:
                        logger.warning("Failed to load chunk %d: %s", i, exc)
                        missing_chunks.append(i)
                else:
                    logger.warning("Chunk file not found: %s", chunk_file)
                    missing_chunks.append(i)

            if successful == 0:
                raise RuntimeError("No valid chunks found")

            if missing_chunks:
                logger.warning("Missing chunks: %s", missing_chunks)

            export_params = {"format": self.settings.audio_format}
            if self.settings.audio_format == "mp3":
                export_params["bitrate"] = self.settings.audio_bitrate

            combined.export(str(output_path), **export_params)
            logger.info(
                "Audiobook saved: %s (%d/%d chunks)",
                output_path,
                successful,
                total_chunks,
            )
            return True

        except Exception as exc:
            logger.error("Failed to combine chunks: %s", exc)
            return False

    def cleanup_temp_chunks(self) -> int:
        """Remove temporary chunk files only (preserve cache)."""
        count = 0
        if self.chunks_dir.exists():
            for chunk_file in self.chunks_dir.glob("chunk_*.wav"):
                try:
                    chunk_file.unlink()
                    count += 1
                except Exception as exc:
                    logger.warning("Failed to delete %s: %s", chunk_file, exc)
        return count

    def restore_chunk_from_cache(self, cache_path: Path, chunk_num: int) -> Path:
        output_path = self.chunks_dir / f"chunk_{chunk_num:04d}.wav"
        shutil.copy2(cache_path, output_path)
        return output_path