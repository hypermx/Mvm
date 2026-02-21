"use client";

import { useState, useCallback } from "react";
import Dashboard from "@/components/Dashboard";
import LogForm from "@/components/LogForm";
import Simulate from "@/components/Simulate";
import Interventions from "@/components/Interventions";
import { getUser, createUser } from "@/lib/api";

type Section = "dashboard" | "log" | "simulate" | "interventions";

interface AlertState {
  msg: string;
  type: "success" | "error";
}

export default function Home() {
  const [section, setSection] = useState<Section>("dashboard");
  const [userId, setUserId] = useState("user_001");
  const [userStatus, setUserStatus] = useState("");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [logCount, setLogCount] = useState(0);

  const showAlert = useCallback((msg: string, type: "success" | "error" = "success") => {
    setAlert({ msg, type });
    setTimeout(() => setAlert(null), 4000);
  }, []);

  async function ensureUser() {
    const id = userId.trim();
    if (!id) { showAlert("Enter a user ID first.", "error"); return; }

    const res = await getUser(id);
    if (res.ok) {
      setUserStatus(`✓ Connected as ${id}`);
      showAlert(`Connected as "${id}".`);
    } else {
      const createRes = await createUser(id);
      if (createRes.ok) {
        setUserStatus(`✓ Created "${id}"`);
        showAlert(`User "${id}" created.`);
      } else {
        showAlert("Failed to create user.", "error");
      }
    }
  }

  const navItems: { id: Section; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "log", label: "Log Today" },
    { id: "simulate", label: "Simulate" },
    { id: "interventions", label: "Interventions" },
  ];

  return (
    <>
      <header>
        <h1>M<span>VM</span></h1>
        <div>
          <div style={{ fontWeight: 600 }}>Migraine Vulnerability Modeling</div>
          <div className="tagline">Threshold-crossing latent state-space model</div>
        </div>
      </header>

      <nav>
        {navItems.map((item) => (
          <button
            key={item.id}
            className={section === item.id ? "active" : ""}
            onClick={() => setSection(item.id)}
          >
            {item.label}
          </button>
        ))}
      </nav>

      <main>
        <div className="user-bar">
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>User ID:</span>
          <input
            type="text"
            placeholder="e.g. user_001"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
          <button className="primary" style={{ marginTop: 0 }} onClick={ensureUser}>
            Connect
          </button>
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>{userStatus}</span>
        </div>

        {alert && <div className={`alert ${alert.type}`}>{alert.msg}</div>}

        {section === "dashboard" && (
          <Dashboard userId={userId} logCount={logCount} onAlert={showAlert} />
        )}
        {section === "log" && (
          <LogForm
            userId={userId}
            onAlert={showAlert}
            onLogSubmitted={() => setLogCount((c) => c + 1)}
          />
        )}
        {section === "simulate" && (
          <Simulate userId={userId} onAlert={showAlert} />
        )}
        {section === "interventions" && (
          <Interventions userId={userId} onAlert={showAlert} />
        )}
      </main>
    </>
  );
}
