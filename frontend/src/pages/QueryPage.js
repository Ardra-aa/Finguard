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
    <div style={{ maxWidth: 860, margin: "0 auto", padding: 24 }}>
      <h2 style={{ color: "#1e3a5f", marginBottom: 4 }}>Compliance Query</h2>
      <p style={{ color: "#64748b", marginBottom: 20, fontSize: 14 }}>
        Querying as <strong>{user.name}</strong> ({user.role} · {user.jurisdiction})
      </p>

      {/* Input */}
      <div style={{ display: "flex", gap: 10, marginBottom: 24 }}>
        <textarea
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && e.ctrlKey) handleSubmit(); }}
          placeholder="Ask a compliance question... (Ctrl+Enter to submit)"
          rows={3}
          style={{
            flex: 1, borderRadius: 8, border: "1px solid #cbd5e1",
            padding: "10px 14px", fontSize: 14, resize: "vertical",
            fontFamily: "inherit",
          }}
        />
        <button
          onClick={handleSubmit}
          disabled={loading || !query.trim()}
          style={{
            background: "#2563eb", color: "#fff", border: "none",
            borderRadius: 8, padding: "0 22px", cursor: "pointer",
            fontWeight: 600, fontSize: 14, alignSelf: "stretch",
            opacity: (loading || !query.trim()) ? 0.5 : 1,
          }}
        >
          {loading ? "..." : "Ask"}
        </button>
      </div>

      {/* Loading */}
      {loading && <Spinner />}

      {/* Blocked error */}
      {error?.type === "blocked" && (
        <div style={{
          background: "#fee2e2", border: "1px solid #fca5a5",
          borderRadius: 8, padding: "16px 20px",
        }}>
          <strong style={{ color: "#991b1b" }}>[BLOCKED] Query Blocked</strong>
          <p style={{ margin: "6px 0 0", fontSize: 14, color: "#374151" }}>
            {error.detail?.error}
          </p>
          {error.detail?.details?.map((d, i) => (
            <p key={i} style={{ margin: "4px 0 0", fontSize: 13, color: "#6b7280" }}>{d}</p>
          ))}
        </div>
      )}

      {/* Generic error */}
      {error?.type === "error" && (
        <div style={{
          background: "#fef3c7", border: "1px solid #fcd34d",
          borderRadius: 8, padding: 14, color: "#92400e", fontSize: 14,
        }}>
          [!] {error.detail}
        </div>
      )}

      {/* Result */}
      {result && (
        <div style={{
          background: "#fff", border: "1px solid #e2e8f0",
          borderRadius: 10, padding: 24,
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 16 }}>
            <ComplianceBadge status={result.compliance_status} />
            <span style={{ fontSize: 12, color: "#94a3b8" }}>
              confidence {(result.confidence_score * 100).toFixed(0)}%
            </span>
          </div>

          <LeakageAlert risk={result.leakage_risk} details={result.leakage_details} />
          <ConflictNotice
            detected={result.conflict_detected}
            conflictingRules={result.conflicting_rules}
            recommendation={result.conservative_recommendation}
          />

          <p style={{ fontSize: 15, color: "#1e293b", lineHeight: 1.6, margin: "0 0 16px" }}>
            {result.answer}
          </p>

          {result.violations?.length > 0 && (
            <div style={{ marginBottom: 12 }}>
              <strong style={{ fontSize: 13, color: "#991b1b" }}>Violations</strong>
              <ul style={{ margin: "4px 0 0", paddingLeft: 18 }}>
                {result.violations.map((v, i) => (
                  <li key={i} style={{ fontSize: 13, color: "#374151" }}>{v}</li>
                ))}
              </ul>
            </div>
          )}

          <SourceCitations sources={result.sources} />
          <AgentTrace trace={result.agent_trace} />
        </div>
      )}

      {/* History */}
      {history.length > 0 && (
        <div style={{ marginTop: 32 }}>
          <h3 style={{ fontSize: 14, color: "#64748b", marginBottom: 12 }}>Recent Queries</h3>
          {history.map((h, i) => (
            <div
              key={i}
              onClick={() => { setQuery(h.query); setResult(h.result); }}
              style={{
                background: "#f8fafc", border: "1px solid #e2e8f0",
                borderRadius: 8, padding: "10px 14px", marginBottom: 8,
                cursor: "pointer", fontSize: 13, color: "#374151",
                display: "flex", justifyContent: "space-between",
              }}
            >
              <span style={{ flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
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
