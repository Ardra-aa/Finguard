// ==========================================================================
// src/pages/QueryPage.js
// Main Compliance Query Interface
// ==========================================================================
// Handles the full query lifecycle:
//   1. User types a compliance question in the textarea
//   2. On submit, sends POST /query to the FastAPI backend
//   3. Displays the response with compliance badge, answer, sources,
//      leakage alerts, conflict notices, and agent trace
//   4. Maintains a clickable history of the last 10 queries
//
// Error handling:
//   - HTTP 403 (blocked): Shows red "Query Blocked" banner with details
//   - Other errors: Shows amber warning banner
// ==========================================================================
import React, { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { postQuery } from "../api/client";
import {
  ComplianceBadge, LeakageAlert, ConflictNotice,
  SourceCitations, AgentTrace, Spinner,
} from "../components";

export function QueryPage() {
  const { user, sessionId } = useAuth();
  const [query, setQuery]       = useState("");
  const [loading, setLoading]   = useState(false);
  const [result, setResult]     = useState(null);
  const [error, setError]       = useState(null);
  const [history, setHistory]   = useState([]);

  async function handleSubmit() {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await postQuery({
        query,
        user_id:      user.user_id,
        role:         user.role,
        jurisdiction: user.jurisdiction,
        session_id:   sessionId,
      });
      setResult(res);
      setHistory(h => [{ query, result: res }, ...h.slice(0, 9)]);
    } catch (err) {
      if (err.status === 403) {
        setError({ type: "blocked", detail: err.detail });
      } else {
        setError({ type: "error", detail: "Request failed. Is the API running?" });
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ maxWidth: 880, margin: "0 auto", padding: "0 24px 48px" }}>
      {/* ── Page Header ────────────────────────────────────────── */}
      <div style={{ marginBottom: 24 }}>
        <h2 style={{
          color: "#0f1f38", marginBottom: 6, fontSize: 22, fontWeight: 700,
          letterSpacing: "-0.01em",
        }}>
          Compliance Query
        </h2>
        <p style={{ color: "#5a6b7f", fontSize: 14, margin: 0 }}>
          Querying as <strong style={{ color: "#1a2332" }}>{user.name}</strong>
          <span style={{
            marginLeft: 8,
            background: "#0f1f38",
            color: "rgba(255,255,255,0.85)",
            borderRadius: 4,
            padding: "2px 8px",
            fontSize: 11,
            fontWeight: 600,
            letterSpacing: "0.02em",
          }}>
            {user.role.replace(/_/g, " ").toUpperCase()}
          </span>
          <span style={{
            marginLeft: 6,
            background: "rgba(232,119,46,0.1)",
            color: "#e8772e",
            borderRadius: 4,
            padding: "2px 8px",
            fontSize: 11,
            fontWeight: 600,
          }}>
            {user.jurisdiction}
          </span>
        </p>
      </div>

      {/* ── Input Area ─────────────────────────────────────────── */}
      <div style={{
        display: "flex", gap: 10, marginBottom: 24,
      }}>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) handleSubmit(); }}
          placeholder="Ask a compliance question... (Ctrl+Enter to submit)"
          rows={3}
          style={{
            flex: 1,
            borderRadius: 8,
            border: "1px solid #d3dce6",
            padding: "12px 16px",
            fontSize: 14,
            resize: "vertical",
            fontFamily: "inherit",
            background: "#ffffff",
            color: "#1a2332",
            outline: "none",
            transition: "border-color 0.2s ease",
          }}
          onFocus={e => e.target.style.borderColor = "#264a73"}
          onBlur={e => e.target.style.borderColor = "#d3dce6"}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          className="fg-btn"
          style={{
            background: "linear-gradient(135deg, #142742 0%, #1a3358 100%)",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "0 24px",
            cursor: "pointer",
            fontWeight: 600,
            fontSize: 14,
            alignSelf: "stretch",
            fontFamily: "inherit",
            opacity: (loading || !query.trim()) ? 0.4 : 1,
            letterSpacing: "0.01em",
            minWidth: 80,
          }}
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {/* ── Loading ────────────────────────────────────────────── */}
      {loading && <Spinner />}

      {/* ── Blocked Error ──────────────────────────────────────── */}
      {error?.type === "blocked" && (
        <div style={{
          background: "#fef2f2",
          border: "1px solid #e8b4b4",
          borderLeft: "4px solid #c53030",
          borderRadius: 8,
          padding: "16px 20px",
          marginBottom: 16,
        }}>
          <strong style={{ color: "#9b2c2c", fontSize: 14 }}>Query Blocked</strong>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "#374151" }}>
            {error.detail?.error}
          </p>
          {error.detail?.details?.map((d, i) => (
            <p key={i} style={{ margin: "4px 0 0", fontSize: 12, color: "#5a6b7f" }}>{d}</p>
          ))}
        </div>
      )}

      {/* ── Generic Error ──────────────────────────────────────── */}
      {error?.type === "error" && (
        <div style={{
          background: "#fffbeb",
          border: "1px solid #e0c97d",
          borderLeft: "4px solid #d69e2e",
          borderRadius: 8,
          padding: "14px 18px",
          color: "#744210",
          fontSize: 13,
          marginBottom: 16,
        }}>
          {error.detail}
        </div>
      )}

      {/* ── Result Card ────────────────────────────────────────── */}
      {result && (
        <div style={{
          background: "#ffffff",
          border: "1px solid #d3dce6",
          borderRadius: 10,
          padding: 24,
          boxShadow: "0 1px 4px rgba(10, 22, 40, 0.06)",
        }}>
          {/* Status row */}
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            marginBottom: 16,
            paddingBottom: 14,
            borderBottom: "1px solid #e4ebf2",
          }}>
            <ComplianceBadge status={result.compliance_status} />
            <span style={{ fontSize: 12, color: "#8896a6" }}>
              Confidence: {(result.confidence_score * 100).toFixed(0)}%
            </span>
          </div>

          {/* Alerts */}
          <LeakageAlert risk={result.leakage_risk} details={result.leakage_details} />
          <ConflictNotice
            detected={result.conflict_detected}
            conflictingRules={result.conflicting_rules}
            recommendation={result.conservative_recommendation}
          />

          {/* Answer */}
          <div style={{
            fontSize: 14, color: "#1a2332", lineHeight: 1.7,
            margin: "0 0 16px",
            whiteSpace: "pre-wrap",
          }}>
            {result.answer}
          </div>

          {/* Violations */}
          {result.violations?.length > 0 && (
            <div style={{
              marginBottom: 14,
              background: "#fef2f2",
              border: "1px solid #e8b4b4",
              borderRadius: 8,
              padding: "12px 16px",
            }}>
              <strong style={{ fontSize: 12, color: "#9b2c2c", letterSpacing: "0.03em" }}>
                VIOLATIONS
              </strong>
              <ul style={{ margin: "6px 0 0", paddingLeft: 18 }}>
                {result.violations.map((v, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 2 }}>{v}</li>
                ))}
              </ul>
            </div>
          )}

          <SourceCitations sources={result.sources} />
          <AgentTrace trace={result.agent_trace} />
        </div>
      )}

      {/* ── Query History ──────────────────────────────────────── */}
      {history.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{
            fontSize: 13, color: "#5a6b7f", marginBottom: 12,
            fontWeight: 600, letterSpacing: "0.04em",
            textTransform: "uppercase",
          }}>
            Recent Queries
          </h3>
          {history.map((h, i) => (
            <div
              key={i}
              onClick={() => { setQuery(h.query); setResult(h.result); }}
              className="fg-card"
              style={{
                background: "#ffffff",
                border: "1px solid #d3dce6",
                borderRadius: 8,
                padding: "10px 16px",
                marginBottom: 8,
                cursor: "pointer",
                fontSize: 13,
                color: "#1a2332",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <span style={{
                flex: 1, overflow: "hidden", textOverflow: "ellipsis",
                whiteSpace: "nowrap", marginRight: 12,
              }}>
                {h.query}
              </span>
              <ComplianceBadge status={h.result?.compliance_status} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
