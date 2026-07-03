"""Intelligent text chunking with sentence boundary detection."""

from __future__ import annotations

import re
from typing import List


def split_into_chunks(text: str, chunk_size_words: int = 1500) -> List[str]:
    """Split text into chunks respecting sentence boundaries."""
    if not text or not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: List[str] = []
    current_chunk = ""
    current_words = 0

    for sentence in sentences:
        sentence_words = len(sentence.split())

        if sentence_words > chunk_size_words:
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_words = 0

            parts = re.split(r"[,;:]", sentence)
            for part in parts:
                part_words = len(part.split())
                if current_words + part_words <= chunk_size_words:
                    current_chunk += part + " "
                    current_words += part_words
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = part + " "
                    current_words = part_words
        else:
            if current_words + sentence_words <= chunk_size_words:
                current_chunk += sentence + " "
                current_words += sentence_words
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
                current_words = sentence_words

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return [chunk for chunk in chunks if chunk.strip()]