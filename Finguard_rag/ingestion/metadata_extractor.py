"""
Finguard_rag/ingestion/metadata_extractor.py
Devna Thunnan — M1: Document Ingestion & Corpus Builder

Reads both metadata JSON files and returns a normalised metadata dict
for any given source filename (PDF or TXT).

Metadata files:
  - data/regulators_metadata.json   — real regulatory PDFs
  - data/corpus/synthetic/synthetic_metadata.json — synthetic policy TXTs
"""

import json
from pathlib import Path
from typing import Optional

# Resolve paths relative to this file's location
_REPO_ROOT = Path(__file__).resolve().parents[2]  # FinGaurd/
_REGULATORS_META = _REPO_ROOT / "data" / "regulators_metadata.json"
_SYNTHETIC_META  = _REPO_ROOT / "data" / "corpus" / "synthetic" / "synthetic_metadata.json"

# Combined lookup: filename -> raw metadata dict
_METADATA_CACHE: dict | None = None


def _load_metadata() -> dict:
    """Load and merge both metadata files into a single filename-keyed dict."""
    global _METADATA_CACHE
    if _METADATA_CACHE is not None:
        return _METADATA_CACHE

    combined: dict = {}

    for meta_path in (_REGULATORS_META, _SYNTHETIC_META):
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                data = json.load(f)
            combined.update(data)
        else:
            print(f"[metadata_extractor] WARNING: metadata file not found: {meta_path}")

    _METADATA_CACHE = combined
    return combined


def get_metadata(filename: str) -> Optional[dict]:
    """
    Return normalised metadata dict for a given source filename.

    Looks up by exact filename (basename only). Returns None if not found.

    Normalised output keys:
        doc_id, jurisdiction (List[str]), regulatory_scope, valid_roles (List[str]),
        effective_date (str ISO), superseded_date (str ISO or None),
        version (str), risk_level (str), risk_score (float)

    Args:
        filename: Basename of the source file, e.g. 'SEBI_LODR_2015.pdf'
                  or 'POL_001_Code_of_Conduct.txt'.

    Returns:
        Metadata dict or None if not found.
    """
    lookup = _load_metadata()
    # Try exact basename match first
    basename = Path(filename).name
    meta = lookup.get(basename) or lookup.get(filename)
    if meta is None:
        return None

    # Return a normalised copy (ensure list types)
    return {
        "doc_id":           meta.get("doc_id", basename),
        "jurisdiction":     meta.get("jurisdiction", ["IN"]),
        "regulatory_scope": meta.get("regulatory_scope", "corporate"),
        "valid_roles":      meta.get("valid_roles", []),
        "effective_date":   meta.get("effective_date", "1970-01-01"),
        "superseded_date":  meta.get("superseded_date", None),
        "version":          str(meta.get("version", "1.0")),
        "risk_level":       meta.get("risk_level", "MEDIUM"),
        "risk_score":       float(meta.get("risk_score", 0.5)),
    }


def get_all_filenames() -> list:
    """Return all registered filenames from both metadata files."""
    return list(_load_metadata().keys())
