"""
M8 — Sensitivity Propagation Graph
Nodes  = query topics (represented by their embeddings + retrieved doc sensitivity)
Edges  = cosine similarity between query embeddings (threshold > 0.35)
Risk   = path-based score across the session's query graph

If any path reconstructs information accessible only to higher-privileged roles
→ leakage_risk is raised to LOW (score >= 0.5) or HIGH (score >= 0.8).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Tuple, Dict


# Documents known to carry restricted/high-sensitivity content
HIGH_SENSITIVITY_DOC_PREFIXES = (
    "BFS-POL-016",   # Salary banding
    "BFS-POL-017",   # ESOP
    "BFS-POL-018",   # M&A policy
    "BFS-POL-014",   # Board thresholds
    "BFS-POL-015",   # Dividend policy
)


@dataclass
class GraphNode:
    query_index: int
    query_text: str
    embedding: List[float]
    sensitivity: str          # "LOW" | "MEDIUM" | "HIGH"
    doc_ids: List[str]


@dataclass
class GraphEdge:
    src: int
    dst: int
    weight: float             # cosine similarity


@dataclass
class SensitivityGraph:
    nodes: List[GraphNode] = field(default_factory=list)
    edges: List[GraphEdge] = field(default_factory=list)

    def add_node(self, node: GraphNode) -> None:
        self.nodes.append(node)

    def add_edge(self, edge: GraphEdge) -> None:
        self.edges.append(edge)

    def adjacency(self) -> Dict[int, List[Tuple[int, float]]]:
        adj: Dict[int, List[Tuple[int, float]]] = {i: [] for i in range(len(self.nodes))}
        for e in self.edges:
            adj[e.src].append((e.dst, e.weight))
            adj[e.dst].append((e.src, e.weight))
        return adj


def _cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    return dot / (na * nb) if na and nb else 0.0


def _doc_sensitivity(doc_ids: List[str]) -> str:
    for doc_id in doc_ids:
        for prefix in HIGH_SENSITIVITY_DOC_PREFIXES:
            if doc_id.startswith(prefix):
                return "HIGH"
    return "LOW"


def build_graph(query_records) -> SensitivityGraph:
    """Construct SensitivityGraph from session's QueryRecord list."""
    graph = SensitivityGraph()

    for idx, rec in enumerate(query_records):
        graph.add_node(GraphNode(
            query_index=idx,
            query_text=rec.query_text,
            embedding=rec.embedding,
            sensitivity=_doc_sensitivity(rec.retrieved_doc_ids),
            doc_ids=rec.retrieved_doc_ids,
        ))

    EDGE_THRESHOLD = 0.35
    for i in range(len(graph.nodes)):
        for j in range(i + 1, len(graph.nodes)):
            sim = _cosine(graph.nodes[i].embedding, graph.nodes[j].embedding)
            if sim >= EDGE_THRESHOLD:
                graph.add_edge(GraphEdge(src=i, dst=j, weight=sim))

    return graph


def compute_leakage_risk(graph: SensitivityGraph) -> Tuple[str, List[str]]:
    """
    Score the graph for leakage risk.
    Returns (risk_level, details_list).
    """
    details: List[str] = []
    if not graph.nodes:
        return "NONE", details

    high_nodes   = [n for n in graph.nodes if n.sensitivity == "HIGH"]
    medium_nodes = [n for n in graph.nodes if n.sensitivity == "MEDIUM"]

    risk_score = 0.0
    risk_score += len(high_nodes)   * 0.4
    risk_score += len(medium_nodes) * 0.15

    adj = graph.adjacency()
    for i in range(len(graph.nodes)):
        for j in range(i + 1, len(graph.nodes)):
            ni, nj = graph.nodes[i], graph.nodes[j]
            if ni.sensitivity == "HIGH" and nj.sensitivity == "HIGH":
                if any(dst == j for dst, _ in adj[i]):
                    risk_score += 0.2
                    details.append(
                        f"Queries {i+1} and {j+1} are semantically linked and both "
                        f"retrieved high-sensitivity documents "
                        f"({ni.doc_ids} / {nj.doc_ids})."
                    )

    all_doc_ids = [d for n in graph.nodes for d in n.doc_ids]
    restricted_hits = sum([
        any("POL-016" in d for d in all_doc_ids),
        any("POL-017" in d for d in all_doc_ids),
        any("POL-018" in d for d in all_doc_ids),
        any("POL-014" in d or "POL-015" in d for d in all_doc_ids),
    ])
    if restricted_hits >= 2:
        risk_score += 0.35
        details.append(
            f"Session touches {restricted_hits} distinct restricted topic areas "
            f"(salary bands, ESOP, M&A, board policy). Cross-query inference attack detected."
        )

    risk_score = min(risk_score, 1.0)

    if risk_score >= 0.8:
        risk_level = "HIGH"
        details.insert(0, f"HIGH leakage risk (score={risk_score:.2f}). Query blocked.")
    elif risk_score >= 0.5:
        risk_level = "LOW"
        details.insert(0, f"LOW leakage risk (score={risk_score:.2f}). Proceed with caution.")
    else:
        risk_level = "NONE"

    return risk_level, details
