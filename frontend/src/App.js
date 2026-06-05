// ==========================================================================
// src/App.js
// FinGuard-RAG Application Shell
// ==========================================================================
// Root component that provides:
//   - AuthProvider context wrapping the entire application
//   - Top navigation bar with "Query" and "Admin" tabs
//   - User info display and sign-out button
//   - Page routing: LoginPage (unauthenticated), QueryPage, AdminPage
//
// Admin tab is only visible to privileged roles:
//   ceo, cfo, compliance_officer, legal_counsel
// ==========================================================================
import React, { useState } from "react";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { LoginPage }  from "./pages/LoginPage";
import { QueryPage }  from "./pages/QueryPage";
import { AdminPage }  from "./pages/AdminPage";

// ── SVG Bank Icon (simple, clean, white) ────────────────────────────────────
function BankIcon({ size = 22 }) {
  return (
    <svg
      width={size} height={size} viewBox="0 0 24 24"
      fill="none" stroke="white" strokeWidth="1.8"
      strokeLinecap="round" strokeLinejoin="round"
      style={{ flexShrink: 0 }}
    >
      {/* Roof triangle */}
      <polygon points="12,2 2,9 22,9" fill="none" />
      {/* Base line */}
      <line x1="2" y1="9" x2="22" y2="9" />
      {/* Pillars */}
      <line x1="6" y1="9" x2="6" y2="17" />
      <line x1="10" y1="9" x2="10" y2="17" />
      <line x1="14" y1="9" x2="14" y2="17" />
      <line x1="18" y1="9" x2="18" y2="17" />
      {/* Foundation */}
      <rect x="2" y="17" width="20" height="2" rx="0.5" fill="none" />
      {/* Steps */}
      <line x1="1" y1="21" x2="23" y2="21" />
      <line x1="3" y1="19" x2="21" y2="19" />
    </svg>
  );
}

function Shell() {
  const { user, logout } = useAuth();
  const [page, setPage] = useState("query");

  if (!user) return <LoginPage />;

  const isAdmin = ["ceo", "cfo", "compliance_officer", "legal_counsel"].includes(user.role);

  const navBtnStyle = (active) => ({
    background: "none",
    border: "none",
    borderBottom: active ? "2px solid #e8772e" : "2px solid transparent",
    color: active ? "#ffffff" : "rgba(255,255,255,0.6)",
    padding: "16px 16px",
    cursor: "pointer",
    fontWeight: active ? 600 : 400,
    fontSize: 14,
    fontFamily: "inherit",
    transition: "color 0.2s ease, border-color 0.2s ease",
    letterSpacing: "0.01em",
  });

  return (
    <div style={{ minHeight: "100vh", background: "#f0f4f8", fontFamily: "'Inter', system-ui, sans-serif" }}>
      {/* ── Dark Blue Header ────────────────────────────────────── */}
      <header style={{
        background: "linear-gradient(135deg, #0a1628 0%, #142742 100%)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        boxShadow: "0 2px 12px rgba(10, 22, 40, 0.25)",
      }}>
        {/* Left: Logo + Nav */}
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{
            display: "flex", alignItems: "center", gap: 10,
            padding: "14px 24px",
          }}>
            <BankIcon size={22} />
            <span style={{
              fontWeight: 700, color: "#ffffff", fontSize: 17,
              letterSpacing: "-0.01em",
            }}>
              FinGuard-RAG
            </span>
          </div>

          {/* Divider */}
          <div style={{
            width: 1, height: 28, background: "rgba(255,255,255,0.12)",
            marginRight: 8,
          }} />

          <nav style={{ display: "flex", gap: 4, padding: "0 8px" }}>
            <button style={navBtnStyle(page === "query")} onClick={() => setPage("query")}>
              Query
            </button>
            {isAdmin && (
              <button style={navBtnStyle(page === "admin")} onClick={() => setPage("admin")}>
                Admin
              </button>
            )}
          </nav>
        </div>

        {/* Right: User info + sign out */}
        <div style={{ display: "flex", alignItems: "center", gap: 14, padding: "0 24px" }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 13, color: "#ffffff", fontWeight: 500 }}>
              {user.name}
            </div>
            <div style={{ fontSize: 11, color: "rgba(255,255,255,0.5)", marginTop: 1 }}>
              {user.role.replace(/_/g, " ")} · {user.jurisdiction}
            </div>
          </div>
          <button
            onClick={logout}
            className="fg-btn"
            style={{
              background: "rgba(255,255,255,0.08)",
              border: "1px solid rgba(255,255,255,0.15)",
              borderRadius: 6,
              padding: "6px 14px",
              cursor: "pointer",
              fontSize: 12,
              color: "rgba(255,255,255,0.75)",
              fontFamily: "inherit",
              fontWeight: 500,
            }}
            onMouseOver={e => e.currentTarget.style.background = "rgba(255,255,255,0.14)"}
            onMouseOut={e => e.currentTarget.style.background = "rgba(255,255,255,0.08)"}
          >
            Sign out
          </button>
        </div>
      </header>

      {/* ── Page Content ────────────────────────────────────────── */}
      <main style={{ paddingTop: 24 }}>
        {page === "query" && <QueryPage />}
        {page === "admin" && isAdmin && <AdminPage />}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Shell />
    </AuthProvider>
  );
}
