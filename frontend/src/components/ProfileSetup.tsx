"use client";

import { useState } from "react";
import { updateUser, UserProfileUpdate } from "@/lib/api";

interface ProfileSetupProps {
  userId: string;
  onComplete: () => void;
}

export default function ProfileSetup({ userId, onComplete }: ProfileSetupProps) {
  const [age, setAge] = useState("");
  const [sex, setSex] = useState("other");
  const [historyYears, setHistoryYears] = useState("");
  const [frequency, setFrequency] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError("");

    const parsedAge = parseInt(age, 10);
    const parsedHistory = parseFloat(historyYears);
    const parsedFrequency = parseFloat(frequency);

    if (isNaN(parsedAge) || parsedAge < 0 || parsedAge > 120) {
      setError("Please enter a valid age (0–120).");
      return;
    }
    if (isNaN(parsedHistory) || parsedHistory < 0) {
      setError("Please enter a valid migraine history duration (years).");
      return;
    }
    if (isNaN(parsedFrequency) || parsedFrequency < 0) {
      setError("Please enter a valid migraine frequency (per month).");
      return;
    }

    setLoading(true);
    try {
      const update: UserProfileUpdate = {
        age: parsedAge,
        sex,
        migraine_history_years: parsedHistory,
        average_migraine_frequency: parsedFrequency,
      };
      await updateUser(userId, update);
      onComplete();
    } catch {
      setError("Could not save your profile. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="card" style={{ maxWidth: 520, margin: "2rem auto" }}>
      <h2 style={{ marginBottom: "0.5rem" }}>Complete Your Profile</h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.9rem", marginBottom: "1.5rem" }}>
        Help us personalize your vulnerability model by providing a few details about your migraine
        history.
      </p>

      {error && <div className="alert error">{error}</div>}

      <form onSubmit={handleSubmit}>
        <div className="field" style={{ marginBottom: "1rem" }}>
          <label>Age</label>
          <input
            type="number"
            value={age}
            onChange={(e) => setAge(e.target.value)}
            placeholder="e.g. 32"
            min={0}
            max={120}
            required
          />
        </div>

        <div className="field" style={{ marginBottom: "1rem" }}>
          <label>Sex</label>
          <select value={sex} onChange={(e) => setSex(e.target.value)} required>
            <option value="female">Female</option>
            <option value="male">Male</option>
            <option value="other">Other / prefer not to say</option>
          </select>
        </div>

        <div className="field" style={{ marginBottom: "1rem" }}>
          <label>Migraine history (years)</label>
          <input
            type="number"
            value={historyYears}
            onChange={(e) => setHistoryYears(e.target.value)}
            placeholder="e.g. 5"
            min={0}
            step="0.5"
            required
          />
        </div>

        <div className="field" style={{ marginBottom: "1.5rem" }}>
          <label>Average migraine frequency (per month)</label>
          <input
            type="number"
            value={frequency}
            onChange={(e) => setFrequency(e.target.value)}
            placeholder="e.g. 2"
            min={0}
            step="0.5"
            required
          />
        </div>

        <button
          type="submit"
          className="primary"
          style={{ width: "100%", marginTop: 0 }}
          disabled={loading}
        >
          {loading ? "Saving…" : "Save & continue"}
        </button>
      </form>
    </div>
  );
}
