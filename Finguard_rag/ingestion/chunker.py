"""
Finguard_rag/ingestion/chunker.py
Devna Thunnan — M1: Document Ingestion & Corpus Builder

Splits raw document text into 512-token chunks with 50-token overlap.
Uses LangChain RecursiveCharacterTextSplitter with character-based sizing
(~4 chars per token: 512 tokens ≈ 2048 chars, 50 tokens ≈ 200 chars).
"""

from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List

# ~4 characters per token is a standard approximation for English legal text
CHARS_PER_TOKEN = 4
CHUNK_TOKENS    = 512
OVERLAP_TOKENS  = 50

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=CHUNK_TOKENS * CHARS_PER_TOKEN,    # 2048 chars ≈ 512 tokens
    chunk_overlap=OVERLAP_TOKENS * CHARS_PER_TOKEN, # 200 chars ≈ 50 tokens
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
    is_separator_regex=False,
)


def chunk_text(text: str) -> List[str]:
    """
    Split a document's full text into overlapping chunks.

    Args:
        text: Raw document text (any length).

    Returns:
        List of text chunk strings, each approximately 512 tokens.
    """
    if not text or not text.strip():
        return []
    return _splitter.split_text(text)
