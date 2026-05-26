// src/api/client.js
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
