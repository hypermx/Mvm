"use client";

import { useState, useCallback } from "react";
import { useSession, signOut } from "next-auth/react";
import Dashboard from "@/components/Dashboard";
import LogForm from "@/components/LogForm";
import Simulate from "@/components/Simulate";
import Interventions from "@/components/Interventions";

type Section = "dashboard" | "log" | "simulate" | "interventions";

interface AlertState {
  msg: string;
  type: "success" | "error";
}

export default function Home() {
  const { data: session } = useSession();
  const userId = (session?.user as { userId?: string })?.userId ?? "";

  const [section, setSection] = useState<Section>("dashboard");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [logCount, setLogCount] = useState(0);

  const showAlert = useCallback((msg: string, type: "success" | "error" = "success") => {
    setAlert({ msg, type });
    setTimeout(() => setAlert(null), 4000);
  }, []);

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
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.75rem" }}>
          <span style={{ color: "var(--text-muted)", fontSize: "0.85rem" }}>
            {session?.user?.email}
          </span>
          <button
            className="primary"
            style={{ marginTop: 0, padding: "0.3rem 0.9rem", fontSize: "0.8rem" }}
            onClick={() => signOut({ callbackUrl: "/login" })}
          >
            Sign out
          </button>
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
