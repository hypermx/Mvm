"use client";

import { useState } from "react";
import { submitLog, DailyLog } from "@/lib/api";

interface LogFormProps {
  userId: string;
  onAlert: (msg: string, type?: "success" | "error") => void;
  onLogSubmitted: () => void;
}

export default function LogForm({ userId, onAlert, onLogSubmitted }: LogFormProps) {
  const today = new Date().toISOString().split("T")[0];

  const [date, setDate] = useState(today);
  const [sleepHours, setSleepHours] = useState(7.5);
  const [sleepQuality, setSleepQuality] = useState(6);
  const [stressLevel, setStressLevel] = useState(4);
  const [hydration, setHydration] = useState(2.0);
  const [caffeine, setCaffeine] = useState(100);
  const [alcohol, setAlcohol] = useState(0);
  const [exercise, setExercise] = useState(20);
  const [pressure, setPressure] = useState(1013.25);
  const [migraineOccurred, setMigraineOccurred] = useState(false);
  const [migraineIntensity, setMigraineIntensity] = useState(5);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!userId) { onAlert("Connect a user first.", "error"); return; }

    const log: DailyLog = {
      date,
      sleep_hours: sleepHours,
      sleep_quality: sleepQuality,
      stress_level: stressLevel,
      hydration_liters: hydration,
      caffeine_mg: caffeine,
      alcohol_units: alcohol,
      exercise_minutes: exercise,
      weather_pressure_hpa: pressure,
      migraine_occurred: migraineOccurred,
      migraine_intensity: migraineOccurred ? migraineIntensity : null,
    };

    setSubmitting(true);
    try {
      const res = await submitLog(userId, log);
      if (res.ok) {
        onAlert("Log submitted successfully!");
        onLogSubmitted();
      } else {
        const err = await res.json();
        onAlert("Error: " + (err.detail || "Unknown error"), "error");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="card">
      <h2>Daily Health Log</h2>
      <form onSubmit={handleSubmit}>
        <div className="form-grid">
          <div className="field">
            <label>Date</label>
            <input type="date" value={date} onChange={(e) => setDate(e.target.value)} required />
          </div>

          <div className="field">
            <label>Sleep Hours</label>
            <div className="range-row">
              <input type="range" min={0} max={12} step={0.5} value={sleepHours}
                onChange={(e) => setSleepHours(parseFloat(e.target.value))} />
              <span>{sleepHours}</span>
            </div>
          </div>

          <div className="field">
            <label>Sleep Quality (0–10)</label>
            <div className="range-row">
              <input type="range" min={0} max={10} step={1} value={sleepQuality}
                onChange={(e) => setSleepQuality(parseInt(e.target.value))} />
              <span>{sleepQuality}</span>
            </div>
          </div>

          <div className="field">
            <label>Stress Level (0–10)</label>
            <div className="range-row">
              <input type="range" min={0} max={10} step={1} value={stressLevel}
                onChange={(e) => setStressLevel(parseInt(e.target.value))} />
              <span>{stressLevel}</span>
            </div>
          </div>

          <div className="field">
            <label>Hydration (liters)</label>
            <div className="range-row">
              <input type="range" min={0} max={5} step={0.25} value={hydration}
                onChange={(e) => setHydration(parseFloat(e.target.value))} />
              <span>{hydration}</span>
            </div>
          </div>

          <div className="field">
            <label>Caffeine (mg)</label>
            <div className="range-row">
              <input type="range" min={0} max={800} step={25} value={caffeine}
                onChange={(e) => setCaffeine(parseFloat(e.target.value))} />
              <span>{caffeine}</span>
            </div>
          </div>

          <div className="field">
            <label>Alcohol (units)</label>
            <div className="range-row">
              <input type="range" min={0} max={10} step={0.5} value={alcohol}
                onChange={(e) => setAlcohol(parseFloat(e.target.value))} />
              <span>{alcohol}</span>
            </div>
          </div>

          <div className="field">
            <label>Exercise (minutes)</label>
            <div className="range-row">
              <input type="range" min={0} max={180} step={5} value={exercise}
                onChange={(e) => setExercise(parseFloat(e.target.value))} />
              <span>{exercise}</span>
            </div>
          </div>

          <div className="field">
            <label>Barometric Pressure (hPa)</label>
            <input type="number" min={950} max={1050} step={0.1} value={pressure}
              onChange={(e) => setPressure(parseFloat(e.target.value))} />
          </div>

          <div className="field">
            <label>Migraine today?</label>
            <select value={migraineOccurred ? "true" : "false"}
              onChange={(e) => setMigraineOccurred(e.target.value === "true")}>
              <option value="false">No</option>
              <option value="true">Yes</option>
            </select>
          </div>

          {migraineOccurred && (
            <div className="field">
              <label>Migraine Intensity (0–10)</label>
              <div className="range-row">
                <input type="range" min={0} max={10} step={1} value={migraineIntensity}
                  onChange={(e) => setMigraineIntensity(parseInt(e.target.value))} />
                <span>{migraineIntensity}</span>
              </div>
            </div>
          )}
        </div>

        <button type="submit" className="primary" disabled={submitting}>
          Submit Log
        </button>
      </form>
    </div>
  );
}
