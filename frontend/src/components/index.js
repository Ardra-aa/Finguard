// src/components/index.js
// All shared UI components

import React from "react";

// ── ComplianceBadge ─────────────────────────────────────────────────────────
export function ComplianceBadge({ status }) {
  const map = {
    PASS:    { bg: "#d1fae5", color: "#065f46", label: "✓ PASS" },
    WARNING: { bg: "#fef3c7", color: "#92400e", label: "⚠ WARNING" },
    FAIL:    { bg: "#fee2e2", color: "#991b1b", label: "✗ FAIL" },
    UNKNOWN: { bg: "#f3f4f6", color: "#374151", label: "? UNKNOWN" },
  };
  const s = map[status] || map.UNKNOWN;
  return (
    <span style={{
      background: s.bg, color: s.color,
      borderRadius: 6, padding: "3px 10px",
      fontWeight: 700, fontSize: 13,
    }}>
      {s.label}
    </span>
  );
}

// ── LeakageAlert ─────────────────────────────────────────────────────────────
export function LeakageAlert({ risk, details = [] }) {
  if (risk === "NONE") return null;
  const isHigh = risk === "HIGH";
  return (
    <div style={{
      background: isHigh ? "#fee2e2" : "#fef3c7",
      border: `1px solid ${isHigh ? "#fca5a5" : "#fcd34d"}`,
      borderRadius: 8, padding: "12px 16px", marginBottom: 12,
    }}>
      <strong style={{ color: isHigh ? "#991b1b" : "#92400e" }}>
        {isHigh ? "🚨 HIGH Leakage Risk" : "⚠ LOW Leakage Risk"}
      </strong>
      {details.map((d, i) => (
        <p key={i} style={{ margin: "4px 0 0", fontSize: 13, color: "#374151" }}>{d}</p>
      ))}
    </div>
  );
}

// ── ConflictNotice ────────────────────────────────────────────────────────────
export function ConflictNotice({ detected, conflictingRules = [], recommendation = "" }) {
  if (!detected) return null;
  return (
    <div style={{
      background: "#eff6ff", border: "1px solid #bfdbfe",
      borderRadius: 8, padding: "12px 16px", marginBottom: 12,
    }}>
      <strong style={{ color: "#1e40af" }}>⚖ Jurisdiction Conflict Detected</strong>
      <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
        {conflictingRules.map((r, i) => (
          <li key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 4 }}>{r}</li>
        ))}
      </ul>
      {recommendation && (
        <div style={{
          marginTop: 10, background: "#dbeafe", borderRadius: 6, padding: "8px 12px",
          fontSize: 13, color: "#1e3a5f",
        }}>
          <strong>Conservative Recommendation:</strong> {recommendation}
        </div>
      )}
    </div>
  );
}

// ── SourceCitations ───────────────────────────────────────────────────────────
export function SourceCitations({ sources = [] }) {
  if (!sources.length) return null;
  return (
    <div style={{ marginTop: 16 }}>
      <strong style={{ fontSize: 13, color: "#374151" }}>Sources</strong>
      <div style={{ marginTop: 6, display: "flex", flexWrap: "wrap", gap: 6 }}>
        {sources.map((s, i) => (
          <span key={i} style={{
            background: "#f3f4f6", border: "1px solid #e5e7eb",
            borderRadius: 6, padding: "3px 10px", fontSize: 12, color: "#374151",
          }}>
            📄 {s.doc_id}
            <span style={{
              marginLeft: 6, fontSize: 11, color: "#6b7280",
            }}>
              [{s.jurisdiction}] {s.risk_level}
            </span>
          </span>
        ))}
      </div>
    </div>
  );
}

// ── AgentTrace ────────────────────────────────────────────────────────────────
export function AgentTrace({ trace = [] }) {
  const [open, setOpen] = React.useState(false);
  if (!trace || !trace.length) return null;
  const typeColors = { THINK: "#7c3aed", ACT: "#0284c7", OBS: "#059669" };

  return (
    <div style={{ marginTop: 16 }}>
      <button
        onClick={() => setOpen(o => !o)}
        style={{
          background: "none", border: "1px solid #d1d5db",
          borderRadius: 6, padding: "4px 12px", cursor: "pointer",
          fontSize: 12, color: "#374151",
        }}
      >
        {open ? "▲ Hide" : "▼ Show"} Agent Trace ({trace.length} steps)
      </button>
      {open && (
        <div style={{ marginTop: 8, borderLeft: "3px solid #e5e7eb", paddingLeft: 12 }}>
          {trace.map((step, i) => (
            <div key={i} style={{ marginBottom: 8 }}>
              <span style={{
                fontWeight: 700, fontSize: 12,
                color: typeColors[step.type] || "#374151",
              }}>
                [{step.type}]
              </span>{" "}
              <span style={{ fontSize: 13, color: "#374151" }}>{step.content}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner() {
  return (
    <div style={{ textAlign: "center", padding: 40 }}>
      <div style={{
        display: "inline-block", width: 36, height: 36,
        border: "4px solid #e5e7eb", borderTopColor: "#2563eb",
        borderRadius: "50%", animation: "spin 0.7s linear infinite",
      }} />
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}
