"""
M8 -- Session Tracker
============================================================================
Per-session query history store (in-memory, thread-safe singleton).

Each session is identified by a unique session_id (generated at login).
The tracker stores all queries made within a session along with their
embeddings, sensitivity classifications, and retrieved document IDs.

Data model:
    SessionTracker (singleton)
      +-- SessionRecord (per session_id)
            +-- QueryRecord (per query within the session)

Used by:
    - LeakageDetector: to build the sensitivity graph across queries
    - API routes: to serve session reports on the admin dashboard
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import threading


@dataclass
class QueryRecord:
    query_text: str
    embedding: List[float]
    sensitivity: str                  # "LOW" | "MEDIUM" | "HIGH"
    retrieved_doc_ids: List[str]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class SessionRecord:
    session_id: str
    user_id: str
    role: str
    queries: List[QueryRecord] = field(default_factory=list)
    leakage_risk: str = "NONE"
    alerts: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class SessionTracker:
    """Singleton in-memory session store."""

    _instance: Optional[SessionTracker] = None
    _lock = threading.Lock()

    def __new__(cls) -> SessionTracker:
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._sessions: Dict[str, SessionRecord] = {}
        return cls._instance

    def get_or_create(self, session_id: str, user_id: str, role: str) -> SessionRecord:
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionRecord(
                session_id=session_id, user_id=user_id, role=role
            )
        return self._sessions[session_id]

    def add_query(self, session_id: str, user_id: str, role: str,
                  query_text: str, embedding: List[float],
                  sensitivity: str, retrieved_doc_ids: List[str]) -> None:
        session = self.get_or_create(session_id, user_id, role)
        session.queries.append(QueryRecord(
            query_text=query_text,
            embedding=embedding,
            sensitivity=sensitivity,
            retrieved_doc_ids=retrieved_doc_ids,
        ))

    def set_leakage_risk(self, session_id: str, risk: str, alert: str = "") -> None:
        if session_id in self._sessions:
            self._sessions[session_id].leakage_risk = risk
            if alert:
                self._sessions[session_id].alerts.append(alert)

    def get_session(self, session_id: str) -> Optional[SessionRecord]:
        return self._sessions.get(session_id)

    def get_queries(self, session_id: str) -> List[QueryRecord]:
        s = self._sessions.get(session_id)
        return s.queries if s else []

    def get_report(self, session_id: str) -> dict:
        s = self._sessions.get(session_id)
        if not s:
            return {"session_id": session_id, "error": "Session not found"}
        return {
            "session_id": session_id,
            "user_id": s.user_id,
            "role": s.role,
            "query_count": len(s.queries),
            "leakage_risk": s.leakage_risk,
            "alerts": s.alerts,
            "queries": [
                {"query": q.query_text, "sensitivity": q.sensitivity, "timestamp": q.timestamp}
                for q in s.queries
            ],
        }

    def get_all_sessions(self) -> list:
        return [
            {
                "session_id": sid,
                "user_id": s.user_id,
                "role": s.role,
                "query_count": len(s.queries),
                "leakage_risk": s.leakage_risk,
                "alerts": s.alerts,
                "created_at": s.created_at,
            }
            for sid, s in self._sessions.items()
        ]

    def clear_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)
