"""Main audiobook conversion orchestrator."""

from __future__ import annotations

import hashlib
import logging
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .audio_processor import AudioProcessor, check_ffmpeg
from .chunker import split_into_chunks
from .progress import ProgressTracker
from .qwen_client import QwenClient
from .settings import Settings
from .text_extractor import TextExtractor

logger = logging.getLogger(__name__)


class QwenAudiobookConverter:
    """Audiobook converter using Qwen Voice API."""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.extractor = TextExtractor(
            clean_page_numbers=settings.clean_page_numbers,
            normalize_whitespace=settings.normalize_whitespace,
        )
        self.qwen: Optional[QwenClient] = None
        self.audio = AudioProcessor(settings)
        self._setup_logging()
        self._setup_directories()

    def _setup_logging(self) -> None:
        Path("logs").mkdir(exist_ok=True)
        handlers = []
        if self.settings.log_to_file:
            log_file = f"logs/audiobook_{datetime.now().strftime('%Y%m%d')}.log"
            handlers.append(logging.FileHandler(log_file, encoding="utf-8"))
        if self.settings.log_to_console:
            handlers.append(logging.StreamHandler(sys.stdout))

        level = getattr(logging, self.settings.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=handlers,
            force=True,
        )

    def _setup_directories(self) -> None:
        for directory in (
            self.settings.books_folder,
            self.settings.audiobooks_folder,
            "chunks",
            "cache/audio_chunks",
            "cache/progress",
            "logs",
        ):
            Path(directory).mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        if self.settings.voice_mode == "voice_clone":
            if not self.settings.voice_clone_ref_audio:
                raise ValueError(
                    "Voice Clone mode requires a reference audio file. "
                    "Use --voice-sample <path>."
                )
            if not Path(self.settings.voice_clone_ref_audio).exists():
                raise FileNotFoundError(
                    f"Reference audio file not found: {self.settings.voice_clone_ref_audio}"
                )

        if not self.settings.dry_run and not check_ffmpeg():
            raise RuntimeError(
                "FFmpeg not found. Install FFmpeg and add it to PATH. "
                "See https://ffmpeg.org/download.html"
            )

    def init_qwen(self) -> None:
        self.qwen = QwenClient(self.settings)
        self.qwen.connect()
        print("[OK] Connected to Qwen API")

        if (
            self.settings.voice_mode == "voice_clone"
            and self.settings.voice_clone_ref_audio
            and not self.settings.voice_clone_ref_text
        ):
            print("[INFO] Transcribing reference audio for voice cloning...")
            text = self.qwen.prepare_voice_clone(self.settings.voice_clone_ref_audio)
            print(f"[OK] Transcription: {text[:100]}...")

    def check_api(self) -> Dict:
        client = QwenClient(self.settings)
        return client.check_health()

    def get_cache_path(self, text: str) -> Path:
        if self.settings.voice_mode == "custom_voice":
            voice_key = self.settings.custom_voice_speaker
            extra = self.settings.custom_voice_instruct
            params = f"{self.settings.custom_voice_model_size}_{self.settings.custom_voice_model_id}_{self.settings.custom_voice_seed}"
        elif self.settings.voice_mode == "voice_clone":
            voice_key = Path(self.settings.voice_clone_ref_audio).name
            extra = ""
            params = f"{self.settings.voice_clone_language}_{self.settings.voice_clone_model_size}_{self.settings.voice_clone_seed}"
        else:
            voice_key = "design"
            extra = self.settings.voice_design_description
            params = f"{self.settings.voice_design_language}_{self.settings.voice_design_seed}"

        content = f"{text}_{self.settings.voice_mode}_{voice_key}_{extra}_{params}"
        digest = hashlib.md5(content.encode()).hexdigest()
        return Path("cache/audio_chunks") / f"{digest}.wav"

    def generate_chunk(self, text: str, chunk_num: int) -> Optional[str]:
        if self.qwen is None:
            raise RuntimeError("Qwen client not initialized")

        cache_path = self.get_cache_path(text)
        if (
            self.settings.enable_caching
            and not self.settings.no_cache
            and cache_path.exists()
        ):
            output = self.audio.restore_chunk_from_cache(cache_path, chunk_num)
            logger.debug("Using cached audio for chunk %d", chunk_num)
            return str(output)

        result = self.qwen.generate(text, self.settings.voice_mode)
        if not result or len(result) < 1:
            raise RuntimeError("Qwen API returned invalid result")

        audio_path = result[0]
        if not audio_path or not Path(audio_path).exists():
            raise RuntimeError(f"Generated audio file not found: {audio_path}")

        output_path = Path("chunks") / f"chunk_{chunk_num:04d}.wav"
        shutil.copy2(audio_path, output_path)

        if self.settings.enable_caching and not self.settings.no_cache:
            shutil.copy2(output_path, cache_path)

        return str(output_path)

    def process_chunk_with_retry(self, chunk_num: int, text: str) -> bool:
        if chunk_num > 1:
            time.sleep(self.settings.min_delay_between_chunks)

        for attempt in range(self.settings.max_retries):
            try:
                result = self.generate_chunk(text, chunk_num)
                if result and Path(result).exists():
                    return True
                logger.warning("Chunk %d attempt %d failed", chunk_num, attempt + 1)
            except Exception as exc:
                logger.warning("Chunk %d attempt %d error: %s", chunk_num, attempt + 1, exc)

            if attempt < self.settings.max_retries - 1:
                sleep_time = 5 + (2**attempt)
                logger.info("Waiting %ds before retry...", sleep_time)
                time.sleep(sleep_time)

        logger.error("Chunk %d failed after %d attempts", chunk_num, self.settings.max_retries)
        return False

    def convert_book(self, file_path: Path) -> bool:
        logger.info("Converting: %s", file_path.name)
        start_time = time.time()

        try:
            logger.info("Extracting text...")
            text = self.extractor.extract(file_path)
            if not text.strip():
                logger.error("No text extracted")
                return False

            word_count = len(text.split())
            logger.info("Extracted %d characters (%d words)", len(text), word_count)

            chunks = split_into_chunks(text, self.settings.chunk_size_words)
            total_chunks = len(chunks)
            if total_chunks == 0:
                logger.error("No chunks created")
                return False

            if self.settings.dry_run:
                self._print_dry_run(file_path, text, chunks)
                return True

            chunk_sizes = [len(c.split()) for c in chunks]
            avg_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            logger.info(
                "Split into %d chunks (avg %.0f words per chunk)",
                total_chunks,
                avg_size,
            )
            print(f"[INFO] Processing {total_chunks} chunks via Qwen API...")
            print(f"[INFO] Estimated time: ~{total_chunks * 4} minutes (4 min per chunk)")

            progress = ProgressTracker(file_path.stem)
            existing = progress.load() if self.settings.resume else None
            settings_hash = self.settings.settings_hash()

            if self.settings.force_restart:
                progress.clear()
                existing = None

            if existing and not existing.is_resumable(settings_hash):
                print(
                    "[WARNING] Settings changed since last run. "
                    "Use --force-restart to ignore saved progress."
                )
                progress.clear()
                existing = None

            if existing is None or not self.settings.resume:
                progress.init(
                    book=file_path.name,
                    total_chunks=total_chunks,
                    voice_mode=self.settings.voice_mode,
                    settings_hash=settings_hash,
                )
            else:
                progress.state = existing
                done = len(existing.completed_chunks)
                print(f"[INFO] Resuming from chunk {done + 1}/{total_chunks}")

            results: Dict[int, bool] = {}
            print(f"\n{'=' * 50}")
            print(f"PROCESSING {total_chunks} CHUNKS")
            print(f"{'=' * 50}")

            for chunk_num, chunk_text in enumerate(chunks, 1):
                if progress.is_complete(chunk_num):
                    cache_chunk = Path("chunks") / f"chunk_{chunk_num:04d}.wav"
                    if not cache_chunk.exists():
                        cache_path = self.get_cache_path(chunk_text)
                        if cache_path.exists():
                            self.audio.restore_chunk_from_cache(cache_path, chunk_num)
                    if cache_chunk.exists():
                        results[chunk_num] = True
                        print(f"[SKIP] Chunk {chunk_num:3d}/{total_chunks} (cached)")
                        continue

                try:
                    ok = self.process_chunk_with_retry(chunk_num, chunk_text)
                    results[chunk_num] = ok
                    if ok:
                        progress.mark_complete(chunk_num)
                        print(f"[OK] Chunk {chunk_num:3d}/{total_chunks} completed")
                    else:
                        progress.mark_failed(chunk_num)
                        print(f"[FAIL] Chunk {chunk_num:3d}/{total_chunks} FAILED")
                except Exception as exc:
                    results[chunk_num] = False
                    progress.mark_failed(chunk_num)
                    print(f"[ERROR] Chunk {chunk_num:3d}/{total_chunks} ERROR: {exc}")

            successful = sum(1 for v in results.values() if v)
            print(f"\n{'=' * 50}")
            print("CHUNK PROCESSING COMPLETE")
            print(f"Successful: {successful}/{total_chunks}")
            print(f"{'=' * 50}")

            if successful == 0:
                self.audio.cleanup_temp_chunks()
                return False

            output_path = (
                Path(self.settings.audiobooks_folder)
                / f"{file_path.stem}.{self.settings.audio_format}"
            )
            success = self.audio.combine_chunks(total_chunks, output_path, results)

            if success:
                elapsed = time.time() - start_time
                minutes, seconds = divmod(int(elapsed), 60)
                print(f"[SUCCESS] Conversion completed in {minutes}m {seconds}s")
                progress.clear()
            else:
                print("[ERROR] Failed to combine chunks into final audiobook")

            self.audio.cleanup_temp_chunks()
            return success

        except Exception as exc:
            logger.error("Conversion failed: %s", exc, exc_info=True)
            self.audio.cleanup_temp_chunks()
            return False

    def _print_dry_run(self, file_path: Path, text: str, chunks: List[str]) -> None:
        print(f"\n[DRY-RUN] File: {file_path.name}")
        print(f"[DRY-RUN] Characters: {len(text)} | Words: {len(text.split())}")
        print(f"[DRY-RUN] Chunks: {len(chunks)} (size={self.settings.chunk_size_words})")
        for i, chunk in enumerate(chunks[:2], 1):
            preview = chunk[:120] + ("..." if len(chunk) > 120 else "")
            print(f"[DRY-RUN] Chunk {i}: {preview}")
        if len(chunks) > 2:
            print(f"[DRY-RUN] ... and {len(chunks) - 2} more chunks")

    def run(self, single_file: Optional[Path] = None) -> Dict[str, bool]:
        self._print_banner()

        supported = self.extractor.get_supported_formats()
        books_dir = Path(self.settings.books_folder)

        if single_file:
            if not single_file.exists():
                print(f"[ERROR] File not found: {single_file}")
                return {str(single_file): False}
            book_files = [single_file]
        else:
            book_files = [
                f
                for f in books_dir.iterdir()
                if f.is_file() and f.suffix.lower() in supported
            ]

        if not book_files:
            print(f"[INFO] No supported files found in {self.settings.books_folder}")
            print(f"Supported formats: {', '.join(supported)}")
            sample = books_dir / "sample.txt"
            if not sample.exists():
                sample.write_text(
                    "This is a sample audiobook for testing the Qwen-based converter. "
                    "Replace this file with your own books to convert.",
                    encoding="utf-8",
                )
                print(f"[INFO] Created sample file: {sample}")
            return {}

        print(f"[INFO] Found {len(book_files)} book(s) to convert")
        results: Dict[str, bool] = {}

        for book_file in book_files:
            try:
                results[book_file.name] = self.convert_book(book_file)
            except KeyboardInterrupt:
                print("\n[WARNING] Conversion interrupted by user")
                break

        self._print_summary(results)
        return results

    def _print_banner(self) -> None:
        print("=" * 70)
        print("QWEN3 AUDIOBOOK CONVERTER")
        print("=" * 70)
        print(f"Books folder: {self.settings.books_folder}")
        print(f"Output folder: {self.settings.audiobooks_folder}")
        print(f"Qwen API: {self.settings.qwen_api_url}")
        print(f"Voice mode: {self.settings.voice_mode}")
        if self.settings.voice_mode == "custom_voice":
            print(f"Speaker: {self.settings.custom_voice_speaker}")
            print(f"Language: {self.settings.custom_voice_language}")
        elif self.settings.voice_mode == "voice_clone":
            ref_name = Path(self.settings.voice_clone_ref_audio).name if self.settings.voice_clone_ref_audio else "N/A"
            print(f"Reference: {ref_name}")
        elif self.settings.voice_mode == "voice_design":
            print(f"Description: {self.settings.voice_design_description[:60]}...")
        print(f"Output format: {self.settings.audio_format}")
        if self.settings.resume:
            print("Resume: enabled")
        if self.settings.dry_run:
            print("Dry-run: enabled")
        print("=" * 70)

    def _print_summary(self, results: Dict[str, bool]) -> None:
        if not results:
            return
        successful = sum(results.values())
        total = len(results)
        print("\n" + "=" * 70)
        print("CONVERSION SUMMARY")
        print("=" * 70)
        print(f"Total: {total} | Success: {successful} | Failed: {total - successful}")
        for filename, ok in results.items():
            print(f"{'[OK]' if ok else '[FAIL]'} {filename}")
        if successful:
            print(f"\n[INFO] Audiobooks saved to: {self.settings.audiobooks_folder}/")