"use client";

import { useState } from "react";
import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");
    setLoading(true);
    const res = await signIn("credentials", {
      email,
      password,
      redirect: false,
    });
    setLoading(false);
    if (res?.error) {
      setError("Invalid email or password.");
    } else {
      router.push("/");
    }
  }

  return (
    <div className="auth-card" style={{ maxWidth: 400 }}>
      <div className="auth-logo">M<span>VM</span></div>
      <p className="auth-subtitle">Sign in to your account</p>

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
        <div className="field" style={{ marginBottom: "1.5rem" }}>
          <label>Password</label>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="••••••••"
            required
            autoComplete="current-password"
          />
        </div>
        <button type="submit" className="primary" style={{ width: "100%", marginTop: 0 }} disabled={loading}>
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p style={{ textAlign: "center", marginTop: "1.5rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
        No account?{" "}
        <Link href="/register" style={{ color: "var(--accent-light)", fontWeight: 500 }}>
          Register
        </Link>
      </p>
    </div>
  );
}
