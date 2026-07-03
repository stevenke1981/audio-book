"""Tests for text chunking."""

from src.chunker import split_into_chunks


def test_empty_text():
    assert split_into_chunks("") == []
    assert split_into_chunks("   ") == []


def test_short_text_single_chunk():
    text = "Hello world. This is a test."
    chunks = split_into_chunks(text, chunk_size_words=100)
    assert len(chunks) == 1
    assert "Hello world" in chunks[0]


def test_sentence_boundary_split():
    sentences = ". ".join(f"Sentence number {i} has several words here" for i in range(20))
    chunks = split_into_chunks(sentences + ".", chunk_size_words=30)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= 30 or "," in chunk or ";" in chunk


def test_long_sentence_secondary_split():
    long_sentence = ", ".join(f"part{i}" for i in range(50))
    chunks = split_into_chunks(long_sentence, chunk_size_words=15)
    assert len(chunks) >= 2


def test_chunk_size_limit():
    sentences = ". ".join(" ".join(f"w{i}" for i in range(8)) for _ in range(15))
    chunks = split_into_chunks(sentences + ".", chunk_size_words=10)
    assert len(chunks) > 1
    for chunk in chunks:
        assert len(chunk.split()) <= 10