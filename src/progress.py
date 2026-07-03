"""Progress persistence for resume support."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Set


@dataclass
class ProgressState:
    book: str
    total_chunks: int
    completed_chunks: List[int] = field(default_factory=list)
    failed_chunks: List[int] = field(default_factory=list)
    voice_mode: str = "custom_voice"
    settings_hash: str = ""
    updated_at: str = ""

    @property
    def completed_set(self) -> Set[int]:
        return set(self.completed_chunks)

    def is_resumable(self, settings_hash: str) -> bool:
        return self.settings_hash == settings_hash and bool(self.completed_chunks)


class ProgressTracker:
    """Track and persist chunk processing progress."""

    def __init__(self, book_stem: str, progress_dir: Path = Path("cache/progress")):
        self.book_stem = book_stem
        self.progress_dir = progress_dir
        self.progress_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.progress_dir / f"{book_stem}.json"
        self.state: Optional[ProgressState] = None

    def load(self) -> Optional[ProgressState]:
        if not self.path.exists():
            return None
        with open(self.path, encoding="utf-8") as f:
            data = json.load(f)
        self.state = ProgressState(**data)
        return self.state

    def init(
        self,
        book: str,
        total_chunks: int,
        voice_mode: str,
        settings_hash: str,
    ) -> ProgressState:
        self.state = ProgressState(
            book=book,
            total_chunks=total_chunks,
            voice_mode=voice_mode,
            settings_hash=settings_hash,
            updated_at=_now_iso(),
        )
        self.save()
        return self.state

    def mark_complete(self, chunk_num: int) -> None:
        if self.state is None:
            raise RuntimeError("Progress not initialized")
        if chunk_num not in self.state.completed_chunks:
            self.state.completed_chunks.append(chunk_num)
            self.state.completed_chunks.sort()
        if chunk_num in self.state.failed_chunks:
            self.state.failed_chunks.remove(chunk_num)
        self.state.updated_at = _now_iso()
        self.save()

    def mark_failed(self, chunk_num: int) -> None:
        if self.state is None:
            raise RuntimeError("Progress not initialized")
        if chunk_num not in self.state.failed_chunks:
            self.state.failed_chunks.append(chunk_num)
        self.state.updated_at = _now_iso()
        self.save()

    def is_complete(self, chunk_num: int) -> bool:
        if self.state is None:
            return False
        return chunk_num in self.state.completed_set

    def save(self) -> None:
        if self.state is None:
            return
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(asdict(self.state), f, indent=2)

    def clear(self) -> None:
        if self.path.exists():
            self.path.unlink()
        self.state = None


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")