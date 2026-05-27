"""
M9 — Jurisdiction-Conflict Resolver
Inspects source documents in each response for conflicting legal regimes
covering the same topic and returns a structured conflict report.
"""

from __future__ import annotations
from typing import List, Optional

from .jurisdiction_ontology import ConflictPattern, get_all_patterns

try:
    from sentence_transformers import SentenceTransformer
    _MODEL = SentenceTransformer("all-MiniLM-L6-v2")
    _EMBED_AVAILABLE = True
except Exception:
    _EMBED_AVAILABLE = False
    _MODEL = None


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _embed(text: str) -> List[float]:
    if _EMBED_AVAILABLE and _MODEL is not None:
        return _MODEL.encode(text, normalize_embeddings=True).tolist()
    import hashlib
    h = hashlib.sha256(text.encode()).digest()
    return [(b / 255.0) for b in h[:32]] + [0.0] * 352


def _keyword_match(text: str, keywords: List[str]) -> bool:
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)


def _doc_hint_match(doc_ids: List[str], hints: List[str]) -> bool:
    for doc_id in doc_ids:
        for hint in hints:
            if hint.lower() in doc_id.lower():
                return True
    return False


class ConflictResolver:
    """
    M9 main class.

    Usage:
        resolver = ConflictResolver()
        result = resolver.resolve(
            query="What are the lease accounting rules?",
            source_doc_ids=["BFS-POL-011", "IndAS_Compendium_2023-chunk-22"],
            source_contents=["Ind AS 116 text...", "IFRS 16 text..."],
            user_jurisdiction="IN",
        )
    """

    def __init__(self) -> None:
        self._patterns = get_all_patterns()
        self._pattern_embeddings: Optional[List[List[float]]] = None

    def _get_pattern_embeddings(self) -> List[List[float]]:
        if self._pattern_embeddings is None:
            self._pattern_embeddings = [
                _embed(p.description + " " + " ".join(p.trigger_keywords))
                for p in self._patterns
            ]
        return self._pattern_embeddings

    def resolve(
        self,
        query: str,
        source_doc_ids: List[str],
        source_contents: List[str],
        user_jurisdiction: str = "IN",
        mock_mode: bool = False,
    ) -> dict:
        """
        Returns:
            {
                "conflict_detected":            bool,
                "conflicting_rules":            List[str],
                "conservative_recommendation":  str,
                "explanation":                  str,
            }
        """
        if mock_mode:
            return {
                "conflict_detected": False,
                "conflicting_rules": [],
                "conservative_recommendation": "",
                "explanation": "",
            }

        combined = query + " " + " ".join(source_contents)
        matched: List[ConflictPattern] = []

        for pattern in self._patterns:
            if _keyword_match(combined, pattern.trigger_keywords):
                matched.append(pattern)
            elif _doc_hint_match(source_doc_ids, pattern.doc_id_hints):
                matched.append(pattern)

        # Semantic similarity fallback
        if not matched and _EMBED_AVAILABLE:
            q_emb = _embed(query)
            for i, p_emb in enumerate(self._get_pattern_embeddings()):
                if _cosine(q_emb, p_emb) > 0.55:
                    matched.append(self._patterns[i])

        # Deduplicate by (jA, jB, topic)
        seen, unique = set(), []
        for p in matched:
            key = (p.jurisdiction_a, p.jurisdiction_b, p.topic)
            if key not in seen:
                seen.add(key)
                unique.append(p)

        if not unique:
            return {
                "conflict_detected": False,
                "conflicting_rules": [],
                "conservative_recommendation": "",
                "explanation": "",
            }

        conflicting_rules = [
            f"{p.jurisdiction_a} vs {p.jurisdiction_b} — {p.topic}: {p.description[:120]}..."
            for p in unique
        ]
        recommendations = [p.conservative_recommendation for p in unique]
        explanations    = [f"[{p.topic.upper()}] {p.description}" for p in unique]

        return {
            "conflict_detected": True,
            "conflicting_rules": conflicting_rules,
            "conservative_recommendation": " | ".join(recommendations),
            "explanation": "\n\n".join(explanations),
        }
