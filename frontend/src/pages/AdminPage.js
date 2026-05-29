// ==========================================================================
// src/pages/AdminPage.js
// Session Monitoring Dashboard (Admin-only)
// ==========================================================================
// Displays all tracked sessions from the backend (/admin/sessions endpoint).
// Each session card shows: user_id, role, session_id, query count, start time,
// and a colour-coded leakage risk badge (NONE=green, LOW=amber, HIGH=red).
//
// Visible only to: ceo, cfo, compliance_officer, legal_counsel
// (access controlled in App.js Shell component)
// ==========================================================================
import React, { useEffect, useState } from "react";
import { getAllSessions } from "../api/client";
import { Spinner } from "../components";

const RISK_COLORS = {
  NONE: { bg: "#d1fae5", color: "#065f46" },
  LOW:  { bg: "#fef3c7", color: "#92400e" },
  HIGH: { bg: "#fee2e2", color: "#991b1b" },
};

export function AdminPage() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState(null);

  useEffect(() => {
    getAllSessions()
      .then(setSessions)
      .catch(() => setError("Could not load sessions. Is the API running?"))
      .finally(() => setLoading(false));
  }, []);

  function refresh() {
    setLoading(true);
    getAllSessions()
      .then(setSessions)
      .catch(() => setError("Refresh failed."))
      .finally(() => setLoading(false));
  }

  return (
    <div style={{ maxWidth: 1000, margin: "0 auto", padding: 24 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 24 }}>
        <h2 style={{ margin: 0, color: "#1e3a5f" }}>Admin -- All Sessions</h2>
        <button
          onClick={refresh}
          style={{
            background: "#2563eb", color: "#fff", border: "none",
            borderRadius: 8, padding: "8px 18px", cursor: "pointer",
            fontSize: 13, fontWeight: 600,
          }}
        >
          Refresh
        </button>
      </div>

      {loading && <Spinner />}
      {error && <p style={{ color: "#991b1b" }}>{error}</p>}

      {!loading && !error && sessions.length === 0 && (
        <p style={{ color: "#64748b" }}>No sessions yet.</p>
      )}

      {sessions.map(s => {
        const rc = RISK_COLORS[s.leakage_risk] || RISK_COLORS.NONE;
        return (
          <div
            key={s.session_id}
            style={{
              background: "#fff", border: "1px solid #e2e8f0",
              borderRadius: 10, padding: "16px 20px", marginBottom: 12,
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div>
                <div style={{ fontWeight: 600, color: "#1e293b", fontSize: 14 }}>
                  {s.user_id}
                </div>
                <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                  {s.role} · Session: {s.session_id} · {s.query_count} queries · Started {s.created_at.slice(0, 19)}
                </div>
              </div>
              <span style={{
                background: rc.bg, color: rc.color,
                borderRadius: 6, padding: "3px 10px", fontWeight: 700, fontSize: 12,
              }}>
                {s.leakage_risk}
              </span>
            </div>
            {s.alerts?.length > 0 && (
              <ul style={{ margin: "10px 0 0", paddingLeft: 20 }}>
                {s.alerts.map((a, i) => (
                  <li key={i} style={{ fontSize: 12, color: "#991b1b", marginBottom: 2 }}>{a}</li>
                ))}
              </ul>
            )}
          </div>
        );
      })}
    </div>
  );
}
