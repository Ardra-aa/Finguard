"""
Finguard_rag/ingestion/ingestor.py
Devna Thunnan — M1: Document Ingestion & Corpus Builder

Main ingestion runner. Walks data/corpus/**/*.pdf and **/*.txt,
extracts text, chunks, embeds, and stores in ChromaDB collection
'finguard_docs' at data/chroma_db/.

All ChromaDB metadata values are stored as strings (ChromaDB requirement).
List fields (jurisdiction, valid_roles) are stored as comma-separated strings.

Run:
    python -m Finguard_rag.ingestion.ingestor
  or from repo root:
    python Finguard_rag/ingestion/ingestor.py
"""

import sys
from pathlib import Path

# Ensure repo root is on the path when run directly
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

import chromadb
import pdfplumber

from Finguard_rag.ingestion.chunker import chunk_text
from Finguard_rag.ingestion.embedder import embed_texts
from Finguard_rag.ingestion.metadata_extractor import get_metadata

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
CORPUS_DIR  = _REPO_ROOT / "data" / "corpus"
CHROMA_PATH = _REPO_ROOT / "data" / "chroma_db"
COLLECTION  = "finguard_docs"

# Fallback metadata for files not registered in either JSON
_FALLBACK_META = {
    "doc_id":           "",
    "jurisdiction":     ["IN"],
    "regulatory_scope": "corporate",
    "valid_roles":      ["compliance_officer", "ceo", "cfo", "legal_counsel",
                         "senior_analyst", "junior_analyst", "it_admin", "auditor_external"],
    "effective_date":   "1970-01-01",
    "superseded_date":  None,
    "version":          "1.0",
    "risk_level":       "MEDIUM",
    "risk_score":       0.5,
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_text_pdf(path: Path) -> str:
    """Extract all text from a PDF using pdfplumber."""
    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                pages.append(text)
    return "\n\n".join(pages)


def _extract_text_txt(path: Path) -> str:
    """Read raw text from a .txt file."""
    return path.read_text(encoding="utf-8", errors="ignore")


def _to_chroma_meta(meta: dict, source_file: str, chunk_index: int) -> dict:
    """
    Convert a normalised metadata dict to a flat ChromaDB-compatible dict.
    All values must be str, int, float, or bool — no lists or None.
    """
    return {
        "doc_id":           meta["doc_id"] or Path(source_file).stem,
        "jurisdiction":     ",".join(meta["jurisdiction"]),          # e.g. "IN,SG"
        "regulatory_scope": meta["regulatory_scope"],
        "valid_roles":      ",".join(meta["valid_roles"]),           # e.g. "cfo,ceo"
        "effective_date":   meta["effective_date"],
        "superseded_date":  meta["superseded_date"] or "",           # "" if current
        "version":          meta["version"],
        "risk_level":       meta["risk_level"],
        "risk_score":       str(meta["risk_score"]),                 # stored as str
        "source_file":      source_file,
        "chunk_index":      chunk_index,
    }


# ---------------------------------------------------------------------------
# Main ingestion
# ---------------------------------------------------------------------------

def ingest(force_reingest: bool = False) -> None:
    """
    Walk the corpus directory, chunk, embed, and upsert into ChromaDB.

    Args:
        force_reingest: If True, drop and recreate the collection before ingesting.
    """
    # 1. Connect to ChromaDB
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))

    if force_reingest:
        try:
            client.delete_collection(COLLECTION)
            print(f"[ingestor] Dropped existing collection '{COLLECTION}'.")
        except Exception:
            pass

    collection = client.get_or_create_collection(
        name=COLLECTION,
        metadata={"hnsw:space": "cosine"},   # cosine similarity for semantic search
    )

    # 2. Discover all corpus files
    pdf_files = list(CORPUS_DIR.rglob("*.pdf"))
    txt_files = list(CORPUS_DIR.rglob("*.txt"))
    all_files = pdf_files + txt_files

    print(f"[ingestor] Found {len(pdf_files)} PDF(s) and {len(txt_files)} TXT(s).")
    print(f"[ingestor] Target collection: '{COLLECTION}' at {CHROMA_PATH}")

    total_chunks = 0

    for file_path in all_files:
        basename = file_path.name
        print(f"\n[ingestor] Processing: {file_path.relative_to(_REPO_ROOT)}")

        # 3. Extract text
        try:
            if file_path.suffix.lower() == ".pdf":
                text = _extract_text_pdf(file_path)
            else:
                text = _extract_text_txt(file_path)
        except Exception as e:
            print(f"  [SKIP] Text extraction failed: {e}")
            continue

        if not text.strip():
            print(f"  [SKIP] Empty text after extraction.")
            continue

        # 4. Chunk text
        chunks = chunk_text(text)
        if not chunks:
            print(f"  [SKIP] No chunks produced.")
            continue
        print(f"  Chunks: {len(chunks)}")

        # 5. Get metadata
        meta = get_metadata(basename)
        if meta is None:
            print(f"  [WARN] No metadata registered for '{basename}'. Using fallback.")
            meta = dict(_FALLBACK_META)
            meta["doc_id"] = Path(basename).stem

        # 6. Embed all chunks in one batch
        embeddings = embed_texts(chunks)

        # 7. Build ChromaDB records
        ids, metas, docs, embeds = [], [], [], []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{meta['doc_id']}__chunk_{i}"
            ids.append(chunk_id)
            metas.append(_to_chroma_meta(meta, basename, i))
            docs.append(chunk)
            embeds.append(emb)

        # 8. Upsert into ChromaDB (upsert = insert or update)
        # Batch in groups of 100 to stay within ChromaDB limits
        BATCH = 100
        for start in range(0, len(ids), BATCH):
            collection.upsert(
                ids=ids[start:start + BATCH],
                embeddings=embeds[start:start + BATCH],
                documents=docs[start:start + BATCH],
                metadatas=metas[start:start + BATCH],
            )

        total_chunks += len(chunks)
        print(f"  Upserted {len(chunks)} chunks -> collection total: {collection.count()}")

    print(f"\n[ingestor] Done. Total chunks ingested: {total_chunks}")
    print(f"[ingestor] Collection '{COLLECTION}' now has {collection.count()} documents.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FinGuard-RAG corpus ingestor")
    parser.add_argument("--force", action="store_true",
                        help="Drop and recreate the ChromaDB collection before ingesting")
    args = parser.parse_args()
    ingest(force_reingest=args.force)
