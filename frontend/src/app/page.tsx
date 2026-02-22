"use client";

import { useState, useCallback, useEffect } from "react";
import { useSession, signOut } from "next-auth/react";
import Dashboard from "@/components/Dashboard";
import LogForm from "@/components/LogForm";
import Simulate from "@/components/Simulate";
import Interventions from "@/components/Interventions";
import ProfileSetup from "@/components/ProfileSetup";
import { getUser, UserProfile, NEW_USER_DEFAULTS } from "@/lib/api";

type Section = "dashboard" | "log" | "simulate" | "interventions";

interface AlertState {
  msg: string;
  type: "success" | "error";
}

function needsProfileSetup(profile: UserProfile): boolean {
  return (
    profile.migraine_history_years === NEW_USER_DEFAULTS.migraine_history_years &&
    profile.average_migraine_frequency === NEW_USER_DEFAULTS.average_migraine_frequency &&
    profile.sex === NEW_USER_DEFAULTS.sex &&
    profile.age === NEW_USER_DEFAULTS.age
  );
}

export default function Home() {
  const { data: session, status } = useSession();
  const userId = (session?.user as { userId?: string })?.userId ?? "";

  const [section, setSection] = useState<Section>("dashboard");
  const [alert, setAlert] = useState<AlertState | null>(null);
  const [logCount, setLogCount] = useState(0);
  const [showProfileSetup, setShowProfileSetup] = useState(false);

  const showAlert = useCallback((msg: string, type: "success" | "error" = "success") => {
    setAlert({ msg, type });
    setTimeout(() => setAlert(null), 4000);
  }, []);

  // Check if new user needs to complete their profile
  useEffect(() => {
    if (!userId) return;
    getUser(userId)
      .then((res) => res.json())
      .then((profile: UserProfile) => {
        if (needsProfileSetup(profile)) {
          setShowProfileSetup(true);
        }
      })
      .catch(() => {
        // If we can't fetch the profile, don't block the UI
      });
  }, [userId]);

  const navItems: { id: Section; label: string }[] = [
    { id: "dashboard", label: "Dashboard" },
    { id: "log", label: "Log Today" },
    { id: "simulate", label: "Simulate" },
    { id: "interventions", label: "Interventions" },
  ];

  if (status === "loading") {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.95rem" }}>Loading…</div>
      </div>
    );
  }

  if (!session) {
    return <LandingPage />;
  }

  return (
    <>
      <header>
        <h1>M<span>VM</span></h1>
        <div>
          <div style={{ fontWeight: 600, fontSize: "0.95rem" }}>Migraine Vulnerability Modeling</div>
          <div className="tagline">Threshold-crossing latent state-space model</div>
        </div>
        <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: "0.75rem" }}>
          {session?.user?.email && (
            <span style={{
              color: "var(--text-muted)",
              fontSize: "0.8rem",
              background: "rgba(124,106,247,0.08)",
              border: "1px solid var(--border-accent)",
              borderRadius: "20px",
              padding: "0.25rem 0.75rem",
            }}>
              {session.user.email}
            </span>
          )}
          <button
            className="primary"
            style={{ marginTop: 0, padding: "0.35rem 1rem", fontSize: "0.8rem" }}
            onClick={() => signOut({ callbackUrl: "/" })}
          >
            Sign out
          </button>
        </div>
      </header>

      {showProfileSetup ? (
        <main>
          <ProfileSetup
            userId={userId}
            onComplete={() => setShowProfileSetup(false)}
          />
        </main>
      ) : (
        <>
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
      )}
    </>
  );
}

