"""Tests for AudioProcessor (mocked, no FFmpeg needed)."""

import logging
from pathlib import Path

import pytest
from pydub import AudioSegment

from src.audio_processor import AudioProcessor
from src.settings import Settings


@pytest.fixture
def processor(tmp_path):
    logging.disable(logging.CRITICAL)
    settings = Settings()
    chunks_dir = tmp_path / "chunks"
    chunks_dir.mkdir()
    proc = AudioProcessor(settings, chunks_dir=chunks_dir)
    yield proc
    logging.disable(logging.NOTSET)


def _create_wav(path: Path, duration_ms: int = 500):
    """Helper to create a minimal valid WAV file."""
    os = __import__("os")
    segment = AudioSegment.silent(duration=duration_ms)
    segment.export(str(path), format="wav")
    return path


def test_combine_chunks_all_success(processor, tmp_path):
    for i in range(1, 4):
        _create_wav(processor.chunks_dir / f"chunk_{i:04d}.wav")
    output = tmp_path / "out.wav"
    result = processor.combine_chunks(
        total_chunks=3,
        output_path=output,
        results={1: True, 2: True, 3: True},
    )
    assert result is True
    assert output.exists()


def test_combine_chunks_partial_missing(processor, tmp_path):
    """Missing chunks should insert silence and still succeed."""
    _create_wav(processor.chunks_dir / "chunk_0001.wav")
    _create_wav(processor.chunks_dir / "chunk_0003.wav")
    output = tmp_path / "partial.wav"
    result = processor.combine_chunks(
        total_chunks=3,
        output_path=output,
        results={1: True, 2: False, 3: True},
    )
    assert result is True
    assert output.exists()


def test_combine_chunks_all_failed(processor, tmp_path):
    output = tmp_path / "fail.wav"
    result = processor.combine_chunks(
        total_chunks=2,
        output_path=output,
        results={1: False, 2: False},
    )
    assert result is False


def test_restore_chunk_from_cache(processor, tmp_path):
    cache_path = tmp_path / "cache.wav"
    _create_wav(cache_path)
    restored = processor.restore_chunk_from_cache(cache_path, 5)
    assert restored == processor.chunks_dir / "chunk_0005.wav"
    assert restored.exists()


def test_cleanup_temp_chunks(processor):
    _create_wav(processor.chunks_dir / "chunk_0001.wav")
    _create_wav(processor.chunks_dir / "chunk_0002.wav")
    # Create a non-chunk file that should be preserved
    (processor.chunks_dir / "keep_me.txt").write_text("data")
    count = processor.cleanup_temp_chunks()
    assert count == 2
    assert (processor.chunks_dir / "keep_me.txt").exists()


def test_combine_chunks_with_no_results_dict(processor, tmp_path):
    """When results is None, all existing chunks should be combined."""
    _create_wav(processor.chunks_dir / "chunk_0001.wav")
    _create_wav(processor.chunks_dir / "chunk_0002.wav")
    output = tmp_path / "all.wav"
    result = processor.combine_chunks(total_chunks=2, output_path=output, results=None)
    assert result is True
    assert output.exists()
