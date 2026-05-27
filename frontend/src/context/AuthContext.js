// src/context/AuthContext.js
import React, { createContext, useContext, useState } from "react";

// 8 demo users from the implementation doc
export const DEMO_USERS = [
  { user_id: "arjun.kumar@bharatfinserv.in",   role: "junior_analyst",      jurisdiction: "IN",     name: "Arjun Kumar" },
  { user_id: "priya.sharma@bharatfinserv.in",  role: "senior_analyst",      jurisdiction: "IN",     name: "Priya Sharma" },
  { user_id: "rajesh.patel@bharatfinserv.in",  role: "compliance_officer",  jurisdiction: "IN",     name: "Rajesh Patel" },
  { user_id: "aisha.nair@bharatfinserv.in",    role: "legal_counsel",       jurisdiction: "IN",     name: "Aisha Nair" },
  { user_id: "vikram.singh@bharatfinserv.in",  role: "cfo",                 jurisdiction: "IN",     name: "Vikram Singh" },
  { user_id: "sunita.rao@bharatfinserv.in",    role: "ceo",                 jurisdiction: "IN",     name: "Sunita Rao" },
  { user_id: "li.wei@bharatfinserv.sg",        role: "senior_analyst",      jurisdiction: "SG",     name: "Li Wei" },
  { user_id: "hans.mueller@bharatfinserv.eu",  role: "compliance_officer",  jurisdiction: "EU",     name: "Hans Mueller" },
];

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [sessionId, setSessionId] = useState(null);

  function login(demoUser) {
    setUser(demoUser);
    setSessionId(`sess-${demoUser.user_id}-${Date.now()}`);
  }

  function logout() {
    setUser(null);
    setSessionId(null);
  }

  return (
    <AuthContext.Provider value={{ user, sessionId, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
