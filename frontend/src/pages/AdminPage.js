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

const RISK_STYLE = {
  NONE: { bg: "rgba(16, 185, 129, 0.1)",  color: "#059669", border: "1px solid rgba(16, 185, 129, 0.2)" },
  LOW:  { bg: "rgba(232, 119, 46, 0.1)",  color: "#e8772e", border: "1px solid rgba(232, 119, 46, 0.2)" },
  HIGH: { bg: "rgba(220, 38, 38, 0.1)",   color: "#dc2626", border: "1px solid rgba(220, 38, 38, 0.2)" },
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
    setError(null);
    getAllSessions()
      .then(setSessions)
      .catch(() => setError("Refresh failed."))
      .finally(() => setLoading(false));
  }

  return (
    <div style={{ maxWidth: 960, margin: "0 auto", padding: "0 24px 48px" }}>
      {/* ── Header Row ─────────────────────────────────────────── */}
      <div style={{
        display: "flex", justifyContent: "space-between", alignItems: "center",
        marginBottom: 24,
      }}>
        <div>
          <h2 style={{
            margin: 0, color: "#0f1f38", fontSize: 22, fontWeight: 700,
            letterSpacing: "-0.01em",
          }}>
            Session Monitor
          </h2>
          <p style={{ margin: "4px 0 0", fontSize: 13, color: "#5a6b7f" }}>
            Active and recent sessions across all users
          </p>
        </div>
        <button
          onClick={refresh}
          className="fg-btn"
          style={{
            background: "linear-gradient(135deg, #142742 0%, #1a3358 100%)",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "8px 20px",
            cursor: "pointer",
            fontSize: 13,
            fontWeight: 600,
            fontFamily: "inherit",
          }}
        >
          Refresh
        </button>
      </div>

      {/* ── Loading / Error / Empty ────────────────────────────── */}
      {loading && <Spinner />}
      {error && (
        <div style={{
          background: "#fef2f2", border: "1px solid #e8b4b4",
          borderLeft: "4px solid #c53030", borderRadius: 8,
          padding: "12px 16px", fontSize: 13, color: "#9b2c2c",
        }}>
          {error}
        </div>
      )}

      {!loading && !error && sessions.length === 0 && (
        <div style={{
          background: "#ffffff", border: "1px solid #d3dce6",
          borderRadius: 10, padding: "40px 24px",
          textAlign: "center", color: "#5a6b7f", fontSize: 14,
        }}>
          No sessions tracked yet. Sessions will appear here once users submit queries.
        </div>
      )}

      {/* ── Session Cards ──────────────────────────────────────── */}
      {sessions.map(s => {
        const rs = RISK_STYLE[s.leakage_risk] || RISK_STYLE.NONE;
        return (
          <div
            key={s.session_id}
            className="fg-card"
            style={{
              background: "#ffffff",
              border: "1px solid #d3dce6",
              borderRadius: 10,
              padding: "18px 22px",
              marginBottom: 12,
              boxShadow: "0 1px 3px rgba(10, 22, 40, 0.04)",
            }}
          >
            <div style={{
              display: "flex", justifyContent: "space-between", alignItems: "flex-start",
            }}>
              <div style={{ flex: 1 }}>
                <div style={{
                  fontWeight: 600, color: "#0f1f38", fontSize: 14,
                }}>
                  {s.user_id}
                </div>
                <div style={{
                  marginTop: 6, display: "flex", flexWrap: "wrap",
                  gap: 8, alignItems: "center",
                }}>
                  <span style={{
                    background: "#0f1f38", color: "rgba(255,255,255,0.85)",
                    borderRadius: 4, padding: "2px 8px",
                    fontSize: 10, fontWeight: 600, letterSpacing: "0.03em",
                    textTransform: "uppercase",
                  }}>
                    {s.role?.replace(/_/g, " ")}
                  </span>
                  <span style={{ fontSize: 12, color: "#5a6b7f" }}>
                    {s.query_count} {s.query_count === 1 ? "query" : "queries"}
                  </span>
                  <span style={{ fontSize: 11, color: "#8896a6" }}>·</span>
                  <span style={{ fontSize: 11, color: "#8896a6" }}>
                    Started {s.created_at?.slice(0, 19)?.replace("T", " ")}
                  </span>
                </div>
                <div style={{
                  marginTop: 4, fontSize: 11, color: "#8896a6",
                  fontFamily: "monospace",
                }}>
                  {s.session_id}
                </div>
              </div>

              {/* Risk Badge */}
              <span style={{
                background: rs.bg, color: rs.color, border: rs.border,
                borderRadius: 6, padding: "4px 12px",
                fontWeight: 700, fontSize: 11,
                letterSpacing: "0.04em",
                flexShrink: 0, marginLeft: 12,
              }}>
                {s.leakage_risk}
              </span>
            </div>

            {/* Alerts */}
            {s.alerts?.length > 0 && (
              <div style={{
                marginTop: 12, paddingTop: 12,
                borderTop: "1px solid #e4ebf2",
              }}>
                {s.alerts.map((a, i) => (
                  <div key={i} style={{
                    fontSize: 12, color: "#9b2c2c", marginBottom: 3,
                    paddingLeft: 12,
                    borderLeft: "2px solid #e8b4b4",
                  }}>
                    {a}
                  </div>
                ))}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
