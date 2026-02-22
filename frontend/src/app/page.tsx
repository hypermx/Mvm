"use client";

import { useState, useCallback } from "react";
import { useSession, signOut, signIn } from "next-auth/react";
import Link from "next/link";
import Dashboard from "@/components/Dashboard";
import LogForm from "@/components/LogForm";
import Simulate from "@/components/Simulate";
import Interventions from "@/components/Interventions";

type Section = "dashboard" | "log" | "simulate" | "interventions";

interface AlertState {
  msg: string;
  type: "success" | "error";
}

const features = [
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <path d="M12 2a10 10 0 1 0 10 10A10 10 0 0 0 12 2z" />
        <polyline points="12 6 12 12 16 14" />
      </svg>
    ),
    title: "Daily Logging",
    desc: "Record sleep, stress, hydration, and other triggers every day to build your personal migraine profile.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
      </svg>
    ),
    title: "Vulnerability Modeling",
    desc: "A threshold-crossing latent state-space model continuously estimates your current migraine risk score.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.07 4.93a10 10 0 0 1 0 14.14M4.93 4.93a10 10 0 0 0 0 14.14" />
      </svg>
    ),
    title: "Intervention Simulation",
    desc: "Test how lifestyle changes—better sleep, reduced caffeine, stress management—would shift your risk trajectory.",
  },
  {
    icon: (
      <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
        <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
        <line x1="3" y1="9" x2="21" y2="9" />
        <line x1="3" y1="15" x2="21" y2="15" />
        <line x1="9" y1="9" x2="9" y2="21" />
        <line x1="15" y1="9" x2="15" y2="21" />
      </svg>
    ),
    title: "Actionable Insights",
    desc: "Track your logged interventions, measure effectiveness over time, and adjust your management strategy.",
  },
];

function LandingPage() {
  return (
    <div className="landing">
      <div className="landing-orb landing-orb-1" />
      <div className="landing-orb landing-orb-2" />

      <header className="landing-header">
        <div className="landing-header-inner">
          <span className="landing-logo">M<span>VM</span></span>
          <div style={{ marginLeft: "auto", display: "flex", gap: "0.75rem" }}>
            <Link href="/login" className="landing-nav-link">Sign in</Link>
            <Link href="/register" className="landing-nav-cta">Get started</Link>
          </div>
        </div>
      </header>

      <section className="landing-hero">
        <div className="landing-badge">Threshold-crossing latent state-space model</div>
        <h1 className="landing-title">
          Understand your<br />
          <span className="landing-title-accent">migraine vulnerability</span>
        </h1>
        <p className="landing-subtitle">
          MVM turns your daily health data into a real-time risk score so you can predict, prevent, and manage migraines—backed by a principled statistical model.
        </p>
        <div className="landing-cta-group">
          <Link href="/register" className="landing-btn-primary">Start for free</Link>
          <Link href="/login" className="landing-btn-secondary">Sign in</Link>
        </div>
      </section>

      <section className="landing-features">
        <h2 className="landing-section-title">Everything you need to stay ahead</h2>
        <div className="landing-grid">
          {features.map((f) => (
            <div key={f.title} className="landing-card">
              <div className="landing-card-icon">{f.icon}</div>
              <h3 className="landing-card-title">{f.title}</h3>
              <p className="landing-card-desc">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="landing-how">
        <h2 className="landing-section-title">How it works</h2>
        <ol className="landing-steps">
          <li className="landing-step">
            <span className="landing-step-num">01</span>
            <div>
              <strong>Create an account</strong>
              <p>Register in seconds—no credit card required.</p>
            </div>
          </li>
          <li className="landing-step">
            <span className="landing-step-num">02</span>
            <div>
              <strong>Log daily factors</strong>
              <p>Record sleep quality, stress, hydration, caffeine, weather changes, and more.</p>
            </div>
          </li>
          <li className="landing-step">
            <span className="landing-step-num">03</span>
            <div>
              <strong>Get your risk score</strong>
              <p>The model updates in real time and shows your current vulnerability as a 0–100% gauge.</p>
            </div>
          </li>
          <li className="landing-step">
            <span className="landing-step-num">04</span>
            <div>
              <strong>Simulate &amp; act</strong>
              <p>Run what-if scenarios and track which interventions actually lower your risk.</p>
            </div>
          </li>
        </ol>
      </section>

      <section className="landing-cta-section">
        <h2 className="landing-cta-heading">Ready to take control?</h2>
        <p className="landing-cta-sub">Join MVM and start understanding your migraine patterns today.</p>
        <div className="landing-cta-group">
          <Link href="/register" className="landing-btn-primary">Create free account</Link>
          <button
            className="landing-btn-secondary"
            onClick={() => signIn(undefined, { callbackUrl: "/" })}
          >
            Sign in with Google
          </button>
        </div>
      </section>

      <footer className="landing-footer">
        <span>© {new Date().getFullYear()} MVM — Migraine Vulnerability Modeling</span>
      </footer>
    </div>
  );
}

export default function Home() {
  const { data: session, status } = useSession();
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
