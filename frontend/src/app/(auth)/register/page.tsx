"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    const res = await fetch("/api/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      const body = await res.json();
      setError(body.error ?? "Registration failed.");
      setLoading(false);
      return;
    }
    // Auto sign-in after registration
    const signInRes = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });
    setLoading(false);
    if (signInRes?.error) {
      setError("Registered but could not sign in automatically. Please log in.");
      router.push("/login");
    } else {
      router.push("/");
    }
  }

  return (
    <div className="auth-card" style={{ maxWidth: 420 }}>
      <div className="auth-logo">M<span>VM</span></div>
      <p className="auth-subtitle">Create your account</p>

      {error && <div className="alert error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="field" style={{ marginBottom: "1rem" }}>
          <label>Email</label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="you@example.com"
            required
            autoComplete="email"
          />
        </div>
        <div className="field" style={{ marginBottom: "1rem" }}>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Min 8 characters"
            required
            autoComplete="new-password"
          />
        </div>
        <div className="field" style={{ marginBottom: "1.5rem" }}>
          <label>Confirm Password</label>
          <input
            type="password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="new-password"
          />
        </div>
        <button type="submit" className="primary" style={{ width: "100%", marginTop: 0 }} disabled={loading}>
          {loading ? "Creating account…" : "Create account"}
        </button>
      </form>

      <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
        Already have an account?{" "}
        <Link href="/login" style={{ color: "var(--accent-light)", fontWeight: 500 }}>
          Sign in
        </Link>
      </p>
    </div>
  );
}
