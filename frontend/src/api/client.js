// ==========================================================================
// src/api/client.js
// HTTP Client for FinGuard-RAG Backend API
// ==========================================================================
// All backend communication goes through these functions.
// Base URL defaults to http://localhost:8000 (configurable via REACT_APP_API_URL).
//
// Functions:
//   postQuery(payload)           -- POST /query (main RAG pipeline)
//   getLeakageReport(sessionId)  -- GET /session/{id}/leakage
//   getAllSessions()             -- GET /admin/sessions
//   getHealth()                  -- GET /health
//
// Error handling:
//   postQuery throws { status, detail } on non-2xx responses so the
//   QueryPage can distinguish 403 (blocked) from other errors.
// ==========================================================================
const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:8000";

export async function postQuery(payload) {
  const res = await fetch(`${BASE_URL}/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw { status: res.status, detail: err.detail };
  }
  return res.json();
}

export async function getLeakageReport(sessionId) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/leakage`);
  if (!res.ok) throw new Error("Session not found");
  return res.json();
}

export async function getAllSessions() {
  const res = await fetch(`${BASE_URL}/admin/sessions`);
  if (!res.ok) throw new Error("Failed to load sessions");
  return res.json();
}

export async function getHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return res.json();
}
