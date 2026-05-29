"""PART 1 — Unit Tests: test_chunker.py"""
import pytest
from Finguard_rag.ingestion.chunker import chunk_text, CHUNK_TOKENS, OVERLAP_TOKENS, CHARS_PER_TOKEN


class TestChunker:
    def test_long_document_splits_into_chunks(self):
        long_text = "word " * 2000  # ~10000 chars >> 2048 chunk_size
        chunks = chunk_text(long_text)
        assert len(chunks) > 1

    def test_each_chunk_within_max_size(self):
        long_text = "Compliance regulation. " * 500
        chunks = chunk_text(long_text)
        max_chars = CHUNK_TOKENS * CHARS_PER_TOKEN
        for chunk in chunks:
            assert len(chunk) <= max_chars + 50  # small tolerance for separator logic

    def test_chunks_overlap_correctly(self):
        long_text = "The quick brown fox jumps over the lazy dog. " * 200
        chunks = chunk_text(long_text)
        if len(chunks) >= 2:
            # The end of chunk[0] should overlap with the start of chunk[1]
            overlap_chars = OVERLAP_TOKENS * CHARS_PER_TOKEN
            tail = chunks[0][-overlap_chars:]
            # At least some overlap text should appear in the next chunk
            assert any(word in chunks[1][:overlap_chars*2] for word in tail.split()[:3])

    def test_short_document_not_split(self):
        short_text = "This is a short document."
        chunks = chunk_text(short_text)
        assert len(chunks) == 1
        assert chunks[0] == short_text

    def test_empty_string_returns_empty(self):
        assert chunk_text("") == []

    def test_none_input_returns_empty(self):
        assert chunk_text(None) == []

    def test_whitespace_only_returns_empty(self):
        assert chunk_text("   \n\n  ") == []

    def test_chunk_preserves_content(self):
        text = "SEBI Regulation 30 requires disclosure. " * 10
        chunks = chunk_text(text)
        combined = " ".join(chunks)
        assert "SEBI Regulation 30" in combined
