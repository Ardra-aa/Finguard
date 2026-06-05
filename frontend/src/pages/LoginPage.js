// ==========================================================================
// src/pages/LoginPage.js
// Demo User Selection Page
// ==========================================================================
// Renders a card with 8 demo user buttons from AuthContext.DEMO_USERS.
// Clicking a user button calls login(demoUser) which sets the active user
// and generates a unique session_id for leakage tracking.
// No password is required -- this is a demo-only authentication flow.
// ==========================================================================
import React from "react";
import { DEMO_USERS, useAuth } from "../context/AuthContext";

// ── Role metadata for display ─────────────────────────────────────────────
const ROLE_META = {
  junior_analyst:      { label: "Junior Analyst",       dept: "Research & Analytics",      level: "Band 6",  icon: "📊" },
  senior_analyst:      { label: "Senior Analyst",       dept: "Research & Analytics",      level: "Band 4",  icon: "📈" },
  compliance_officer:  { label: "Compliance Officer",   dept: "Compliance & Risk",         level: "Band 2",  icon: "🛡️" },
  legal_counsel:       { label: "Legal Counsel",        dept: "Legal & Regulatory",        level: "Band 2",  icon: "⚖️" },
  cfo:                 { label: "Chief Financial Officer", dept: "Executive Leadership",   level: "Band 1",  icon: "💼" },
  ceo:                 { label: "Chief Executive Officer", dept: "Executive Leadership",   level: "Band 1",  icon: "🏛️" },
  it_admin:            { label: "IT Administrator",     dept: "Information Technology",     level: "Band 3",  icon: "🖥️" },
  auditor_external:    { label: "External Auditor",     dept: "Audit & Assurance",         level: "External", icon: "🔍" },
};

const JURISDICTION_META = {
  IN: { label: "India",       flag: "🇮🇳" },
  SG: { label: "Singapore",   flag: "🇸🇬" },
  EU: { label: "European Union", flag: "🇪🇺" },
};

// ── Bank Icon for login header ────────────────────────────────────────────
function BankIcon({ size = 28 }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="white" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round"
    >
      <polygon points="12,2 2,9 22,9" fill="none" />
      <line x1="2" y1="9" x2="22" y2="9" />
      <line x1="6" y1="9" x2="6" y2="17" />
      <line x1="10" y1="9" x2="10" y2="17" />
      <line x1="14" y1="9" x2="14" y2="17" />
      <line x1="18" y1="9" x2="18" y2="17" />
      <rect x="2" y="17" width="20" height="2" rx="0.5" fill="none" />
      <line x1="1" y1="21" x2="23" y2="21" />
      <line x1="3" y1="19" x2="21" y2="19" />
    </svg>
  );
}

export function LoginPage() {
  const { login } = useAuth();

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(160deg, #0a1628 0%, #142742 40%, #1a3358 100%)",
      padding: 24,
    }}>
      <div style={{ width: 560, maxWidth: "100%" }}>
        {/* ── Header ────────────────────────────────────────────── */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 12,
            marginBottom: 8,
          }}>
            <BankIcon size={32} />
            <h1 style={{
              margin: 0, color: "#ffffff", fontSize: 26,
              fontWeight: 700, letterSpacing: "-0.02em",
            }}>
              FinGuard-RAG
            </h1>
          </div>
          <p style={{
            margin: "8px 0 0", color: "rgba(255,255,255,0.45)", fontSize: 13,
            fontWeight: 400,
          }}>
            BharatFinServ Ltd. — Compliance Portal
          </p>
          <p style={{
            margin: "16px 0 0", color: "rgba(255,255,255,0.6)", fontSize: 14,
          }}>
            Select a demo user to continue
          </p>
        </div>

        {/* ── User Role Cards ───────────────────────────────────── */}
        <div style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: 12,
        }}>
          {DEMO_USERS.map(u => {
            const meta = ROLE_META[u.role] || { label: u.role, dept: "", level: "", icon: "👤" };
            const jur = JURISDICTION_META[u.jurisdiction] || { label: u.jurisdiction, flag: "🌐" };

            return (
              <button
                key={u.user_id}
                onClick={() => login(u)}
                className="fg-card"
                style={{
                  background: "rgba(255,255,255,0.04)",
                  border: "1px solid rgba(255,255,255,0.10)",
                  borderRadius: 10,
                  padding: "16px 18px",
                  cursor: "pointer",
                  textAlign: "left",
                  fontFamily: "inherit",
                  display: "flex",
                  gap: 14,
                  alignItems: "flex-start",
                }}
                onMouseOver={e => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.08)";
                  e.currentTarget.style.borderColor = "rgba(232,119,46,0.4)";
                }}
                onMouseOut={e => {
                  e.currentTarget.style.background = "rgba(255,255,255,0.04)";
                  e.currentTarget.style.borderColor = "rgba(255,255,255,0.10)";
                }}
              >
                {/* Icon */}
                <div style={{
                  fontSize: 22, lineHeight: 1,
                  width: 40, height: 40,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  background: "rgba(255,255,255,0.06)",
                  borderRadius: 8, flexShrink: 0,
                }}>
                  {meta.icon}
                </div>

                {/* Details */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{
                    fontWeight: 600, color: "#ffffff", fontSize: 14,
                    marginBottom: 4,
                  }}>
                    {u.name}
                  </div>
                  <div style={{
                    fontSize: 12, color: "rgba(255,255,255,0.55)",
                    lineHeight: 1.5,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                      <span>{meta.label}</span>
                      <span style={{
                        fontSize: 10, color: "#e8772e",
                        fontWeight: 600, letterSpacing: "0.03em",
                      }}>
                        {meta.level}
                      </span>
                    </div>
                    <div style={{ marginTop: 2, color: "rgba(255,255,255,0.35)" }}>
                      {meta.dept}
                    </div>
                    <div style={{
                      marginTop: 4,
                      display: "flex", alignItems: "center", gap: 6,
                      fontSize: 11, color: "rgba(255,255,255,0.4)",
                    }}>
                      <span>{jur.flag}</span>
                      <span>{jur.label}</span>
                      <span style={{ margin: "0 2px" }}>·</span>
                      <span style={{
                        overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap",
                      }}>
                        {u.user_id}
                      </span>
                    </div>
                  </div>
                </div>
              </button>
            );
          })}
        </div>

        {/* ── Footer ────────────────────────────────────────────── */}
        <p style={{
          marginTop: 24, textAlign: "center",
          fontSize: 11, color: "rgba(255,255,255,0.25)",
        }}>
          Demo environment — no credentials required
        </p>
      </div>
    </div>
  );
}
