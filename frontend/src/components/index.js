// ==========================================================================
// src/components/index.js
// Shared UI Components for FinGuard-RAG Frontend
// ==========================================================================
// Exports:
//   ComplianceBadge  -- Colour-coded PASS/WARNING/FAIL badge
//   LeakageAlert     -- Leakage risk notification banner
//   ConflictNotice   -- Jurisdiction conflict warning with recommendations
//   SourceCitations  -- Document citation pills with jurisdiction info
//   AgentTrace       -- Collapsible agent reasoning trace viewer
//   Spinner          -- Loading animation
// ==========================================================================

import React from "react";

// ── ComplianceBadge ─────────────────────────────────────────────────────────
export function ComplianceBadge({ status }) {
  const map = {
    PASS:    { bg: "rgba(16, 185, 129, 0.1)",  color: "#059669", border: "1px solid rgba(16, 185, 129, 0.25)", label: "PASS" },
    WARNING: { bg: "rgba(232, 119, 46, 0.1)",  color: "#e8772e", border: "1px solid rgba(232, 119, 46, 0.25)", label: "WARNING" },
    FAIL:    { bg: "rgba(220, 38, 38, 0.1)",   color: "#dc2626", border: "1px solid rgba(220, 38, 38, 0.25)",  label: "FAIL" },
    UNKNOWN: { bg: "rgba(90, 107, 127, 0.08)", color: "#5a6b7f", border: "1px solid rgba(90, 107, 127, 0.15)", label: "UNKNOWN" },
  };
  const s = map[status] || map.UNKNOWN;
  return (
    <span style={{
      background: s.bg, color: s.color, border: s.border,
      borderRadius: 5, padding: "3px 10px",
      fontWeight: 700, fontSize: 11,
      letterSpacing: "0.04em",
      display: "inline-block",
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
      background: isHigh ? "#fef2f2" : "rgba(232, 119, 46, 0.06)",
      border: `1px solid ${isHigh ? "#e8b4b4" : "rgba(232, 119, 46, 0.2)"}`,
      borderLeft: `4px solid ${isHigh ? "#dc2626" : "#e8772e"}`,
      borderRadius: 8, padding: "12px 16px", marginBottom: 14,
    }}>
      <strong style={{
        color: isHigh ? "#9b2c2c" : "#e8772e",
        fontSize: 13, letterSpacing: "0.02em",
      }}>
        {isHigh ? "HIGH Leakage Risk Detected" : "Low Leakage Risk"}
      </strong>
      {details.map((d, i) => (
        <p key={i} style={{ margin: "6px 0 0", fontSize: 13, color: "#374151", lineHeight: 1.5 }}>{d}</p>
      ))}
    </div>
  );
}

// ── ConflictNotice ────────────────────────────────────────────────────────────
export function ConflictNotice({ detected, conflictingRules = [], recommendation = "" }) {
  if (!detected) return null;
  return (
    <div style={{
      background: "rgba(20, 39, 66, 0.04)",
      border: "1px solid rgba(20, 39, 66, 0.12)",
      borderLeft: "4px solid #264a73",
      borderRadius: 8, padding: "14px 18px", marginBottom: 14,
    }}>
      <strong style={{ color: "#142742", fontSize: 13, letterSpacing: "0.02em" }}>
        Jurisdiction Conflict Detected
      </strong>
      <ul style={{ margin: "8px 0 0", paddingLeft: 18 }}>
        {conflictingRules.map((r, i) => (
          <li key={i} style={{ fontSize: 13, color: "#374151", marginBottom: 4, lineHeight: 1.5 }}>{r}</li>
        ))}
      </ul>
      {recommendation && (
        <div style={{
          marginTop: 12,
          background: "rgba(232, 119, 46, 0.06)",
          border: "1px solid rgba(232, 119, 46, 0.15)",
          borderRadius: 6,
          padding: "10px 14px",
          fontSize: 13,
          color: "#1a2332",
          lineHeight: 1.5,
        }}>
          <strong style={{ color: "#e8772e", fontSize: 11, letterSpacing: "0.04em" }}>
            CONSERVATIVE RECOMMENDATION
          </strong>
          <div style={{ marginTop: 4 }}>{recommendation}</div>
        </div>
      )}
    </div>
  );
}

// ── SourceCitations ───────────────────────────────────────────────────────────
export function SourceCitations({ sources = [] }) {
  if (!sources.length) return null;
  return (
    <div style={{
      marginTop: 16,
      paddingTop: 14,
      borderTop: "1px solid #e4ebf2",
    }}>
      <strong style={{
        fontSize: 11, color: "#5a6b7f",
        letterSpacing: "0.04em", textTransform: "uppercase",
      }}>
        Sources
      </strong>
      <div style={{ marginTop: 8, display: "flex", flexWrap: "wrap", gap: 8 }}>
        {sources.map((s, i) => (
          <span key={i} style={{
            background: "rgba(20, 39, 66, 0.04)",
            border: "1px solid #d3dce6",
            borderRadius: 6,
            padding: "5px 12px",
            fontSize: 12,
            color: "#0f1f38",
            fontWeight: 500,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
          }}>
            <span style={{ fontFamily: "monospace", fontSize: 11 }}>{s.doc_id}</span>
            <span style={{
              fontSize: 10, color: "#5a6b7f",
              borderLeft: "1px solid #d3dce6",
              paddingLeft: 8,
            }}>
              {s.jurisdiction} · {s.risk_level}
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

  const typeColors = {
    THINK: "#6d28d9",
    ACT:   "#264a73",
    OBS:   "#059669",
  };

  return (
    <div style={{ marginTop: 16, paddingTop: 14, borderTop: "1px solid #e4ebf2" }}>
      <button
        onClick={() => setOpen(o => !o)}
        className="fg-btn"
        style={{
          background: "rgba(20, 39, 66, 0.04)",
          border: "1px solid #d3dce6",
          borderRadius: 6,
          padding: "5px 14px",
          cursor: "pointer",
          fontSize: 12,
          color: "#0f1f38",
          fontWeight: 500,
          fontFamily: "inherit",
        }}
      >
        {open ? "▾ Hide" : "▸ Show"} Agent Trace ({trace.length} steps)
      </button>
      {open && (
        <div style={{
          marginTop: 10,
          borderLeft: "3px solid #264a73",
          paddingLeft: 14,
        }}>
          {trace.map((step, i) => (
            <div key={i} style={{ marginBottom: 10 }}>
              <span style={{
                fontWeight: 700, fontSize: 11,
                color: typeColors[step.type] || "#374151",
                letterSpacing: "0.04em",
                background: `${typeColors[step.type] || "#374151"}15`,
                padding: "1px 6px", borderRadius: 3,
              }}>
                {step.type}
              </span>{" "}
              <span style={{ fontSize: 13, color: "#1a2332", lineHeight: 1.5 }}>
                {step.content}
              </span>
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
        border: "3px solid #d3dce6",
        borderTopColor: "#142742",
        borderRadius: "50%",
        animation: "fg-spin 0.7s linear infinite",
      }} />
    </div>
  );
}
