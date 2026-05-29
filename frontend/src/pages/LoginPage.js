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

export function LoginPage() {
  const { login } = useAuth();
  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center",
      justifyContent: "center", background: "#f8fafc",
    }}>
      <div style={{
        background: "#fff", borderRadius: 12, padding: 40,
        boxShadow: "0 4px 24px rgba(0,0,0,0.08)", width: 480,
      }}>
        <h1 style={{ margin: "0 0 4px", color: "#1e3a5f", fontSize: 24 }}>FinGuard-RAG</h1>
        <p style={{ margin: "0 0 28px", color: "#6b7280", fontSize: 14 }}>
          Select a demo user to continue
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
          {DEMO_USERS.map(u => (
            <button
              key={u.user_id}
              onClick={() => login(u)}
              style={{
                background: "#f8fafc", border: "1px solid #e2e8f0",
                borderRadius: 8, padding: "12px 16px", cursor: "pointer",
                textAlign: "left", transition: "background 0.15s",
              }}
              onMouseOver={e => e.currentTarget.style.background = "#eff6ff"}
              onMouseOut={e => e.currentTarget.style.background = "#f8fafc"}
            >
              <div style={{ fontWeight: 600, color: "#1e293b", fontSize: 14 }}>{u.name}</div>
              <div style={{ fontSize: 12, color: "#64748b", marginTop: 2 }}>
                {u.role} · {u.jurisdiction} · {u.user_id}
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
