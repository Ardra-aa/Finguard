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

const NAV_STYLE = {
  display: "flex", gap: 8, padding: "0 24px",
};
const NAV_BTN = (active) => ({
  background: active ? "#eff6ff" : "none",
  border: "none",
  borderBottom: active ? "2px solid #2563eb" : "2px solid transparent",
  color: active ? "#2563eb" : "#475569",
  padding: "14px 12px",
  cursor: "pointer",
  fontWeight: active ? 700 : 400,
  fontSize: 14,
});

function Shell() {
  const { user, logout } = useAuth();
  const [page, setPage] = useState("query");

  if (!user) return <LoginPage />;

  const isAdmin = ["ceo", "cfo", "compliance_officer", "legal_counsel"].includes(user.role);

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "Inter, system-ui, sans-serif" }}>
      {/* Top bar */}
      <div style={{
        background: "#fff", borderBottom: "1px solid #e2e8f0",
        display: "flex", justifyContent: "space-between", alignItems: "center",
      }}>
        <div style={{ display: "flex", alignItems: "center" }}>
          <span style={{
            padding: "16px 24px", fontWeight: 800, color: "#1e3a5f", fontSize: 18,
          }}>
            FinGuard
          </span>
          <nav style={NAV_STYLE}>
            <button style={NAV_BTN(page === "query")} onClick={() => setPage("query")}>
              Query
            </button>
            {isAdmin && (
              <button style={NAV_BTN(page === "admin")} onClick={() => setPage("admin")}>
                Admin
              </button>
            )}
          </nav>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12, padding: "0 24px" }}>
          <span style={{ fontSize: 13, color: "#64748b" }}>
            {user.name} · <strong>{user.role}</strong>
          </span>
          <button
            onClick={logout}
            style={{
              background: "none", border: "1px solid #cbd5e1", borderRadius: 6,
              padding: "6px 14px", cursor: "pointer", fontSize: 13, color: "#475569",
            }}
          >
            Sign out
          </button>
        </div>
      </div>

      {/* Page content */}
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
