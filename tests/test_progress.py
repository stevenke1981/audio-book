"""Tests for progress persistence."""

from src.progress import ProgressState, ProgressTracker


def test_init_and_mark_complete(tmp_path):
    tracker = ProgressTracker("test_book", progress_dir=tmp_path)
    state = tracker.init(
        book="test.pdf",
        total_chunks=5,
        voice_mode="custom_voice",
        settings_hash="abc123",
    )
    assert state.total_chunks == 5
    assert state.completed_chunks == []

    tracker.mark_complete(1)
    tracker.mark_complete(3)
    assert tracker.is_complete(1)
    assert tracker.is_complete(3)
    assert not tracker.is_complete(2)


def test_load_saved_progress(tmp_path):
    tracker = ProgressTracker("resume_book", progress_dir=tmp_path)
    tracker.init("book.epub", 10, "custom_voice", "hash1")
    tracker.mark_complete(1)
    tracker.mark_complete(2)
    tracker.save()

    loaded = ProgressTracker("resume_book", progress_dir=tmp_path)
    state = loaded.load()
    assert state is not None
    assert state.completed_chunks == [1, 2]
    assert state.total_chunks == 10


def test_is_resumable_requires_matching_hash():
    state = ProgressState(
        book="a.txt",
        total_chunks=3,
        completed_chunks=[1],
        settings_hash="old_hash",
    )
    assert state.is_resumable("old_hash")
    assert not state.is_resumable("new_hash")


def test_mark_failed(tmp_path):
    tracker = ProgressTracker("fail_book", progress_dir=tmp_path)
    tracker.init("book.txt", 3, "custom_voice", "h")
    tracker.mark_failed(2)
    assert 2 in tracker.state.failed_chunks