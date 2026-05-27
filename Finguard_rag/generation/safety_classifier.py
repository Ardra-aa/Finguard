"""
Finguard_rag/generation/safety_classifier.py
Amala P Ansalem — M6 Layer B: Neural Safety Classifier

Computes cosine similarity between each sentence of the LLM response and
the known non-compliant patterns from noncompliant_patterns.py.

Uses sentence-transformers (all-MiniLM-L6-v2) — the same model used for
document embeddings — so no additional download is needed.

Threshold: 0.82 (from config.yaml: compliance.noncompliant_pattern_threshold)
    - cosine >= 0.82 → flag the sentence as WARNING
    - cosine >= 0.92 → escalate to HIGH (near-verbatim match)
"""

import sys
import re
import logging
from typing import List, Dict, Tuple, Optional
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from Finguard_rag.generation.noncompliant_patterns import get_pattern_texts

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load config
# ---------------------------------------------------------------------------
_CONFIG_PATH = _REPO_ROOT / "config.yaml"


def _load_threshold() -> float:
    """Load the cosine similarity threshold from config.yaml."""
    if _CONFIG_PATH.exists():
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cfg.get("compliance", {}).get(
            "noncompliant_pattern_threshold", 0.82
        )
    return 0.82


THRESHOLD = _load_threshold()

# ---------------------------------------------------------------------------
# Lazy-loaded sentence-transformer model and pattern embeddings
# ---------------------------------------------------------------------------
_model = None
_pattern_embeddings = None


def _get_model():
    """Lazily load the sentence-transformer model (first call ~2-3 s)."""
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        model_name = "sentence-transformers/all-MiniLM-L6-v2"
        logger.info("Loading sentence-transformer model: %s", model_name)
        _model = SentenceTransformer(model_name)
    return _model


def _get_pattern_embeddings():
    """Lazily embed all non-compliant patterns (once per process)."""
    global _pattern_embeddings
    if _pattern_embeddings is None:
        model = _get_model()
        texts = get_pattern_texts()
        logger.info("Embedding %d non-compliant patterns …", len(texts))
        _pattern_embeddings = model.encode(texts, normalize_embeddings=True)
    return _pattern_embeddings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _split_sentences(text: str) -> List[str]:
    """
    Split text into sentences using a simple regex.
    Keeps sentences with at least 10 characters to avoid noise.
    """
    raw = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in raw if len(s.strip()) >= 10]


def _cosine_similarity_batch(
    query_embedding,
    corpus_embeddings,
):
    """
    Compute cosine similarities between a single query embedding
    and a matrix of corpus embeddings.

    Both inputs are assumed to be L2-normalised (so dot product = cosine).
    Returns a 1-D array of similarity scores.
    """
    import numpy as np
    return np.dot(corpus_embeddings, query_embedding)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def classify_safety(
    response_text: str,
    mock_mode: bool = False,
) -> Dict:
    """
    Run the neural safety classifier against the LLM response.

    For each sentence in ``response_text``, compute cosine similarity
    against every known non-compliant pattern.  If any similarity
    exceeds the threshold (default 0.82), flag a warning.

    Args:
        response_text: The raw LLM answer string.
        mock_mode:     If True, skip the model and return a clean result.

    Returns:
        A dict with keys:
            - ``flagged``   (bool):  True if any sentence exceeded the threshold.
            - ``max_score`` (float): Highest cosine similarity found.
            - ``matches``   (List[Dict]): Details of each flagged sentence:
                  ``{"sentence": str, "pattern": str, "score": float}``
    """
    if mock_mode:
        return {"flagged": False, "max_score": 0.0, "matches": []}

    sentences = _split_sentences(response_text)
    if not sentences:
        return {"flagged": False, "max_score": 0.0, "matches": []}

    model = _get_model()
    pattern_embeddings = _get_pattern_embeddings()
    pattern_texts = get_pattern_texts()

    # Encode all response sentences at once
    sentence_embeddings = model.encode(sentences, normalize_embeddings=True)

    matches: List[Dict] = []
    global_max = 0.0

    for sent_idx, sent_emb in enumerate(sentence_embeddings):
        scores = _cosine_similarity_batch(sent_emb, pattern_embeddings)
        max_idx = int(scores.argmax())
        max_score = float(scores[max_idx])

        if max_score > global_max:
            global_max = max_score

        if max_score >= THRESHOLD:
            matches.append({
                "sentence": sentences[sent_idx],
                "pattern": pattern_texts[max_idx],
                "score": round(max_score, 4),
            })
            logger.warning(
                "Neural safety flag: score=%.4f  sentence='%s…'  pattern='%s…'",
                max_score,
                sentences[sent_idx][:60],
                pattern_texts[max_idx][:60],
            )

    return {
        "flagged": len(matches) > 0,
        "max_score": round(global_max, 4),
        "matches": matches,
    }
