"use client";

import { useState } from "react";
import TrajectoryChart from "./TrajectoryChart";
import { runSimulation, SimulationResult } from "@/lib/api";

interface SimulateProps {
  userId: string;
  onAlert: (msg: string, type?: "success" | "error") => void;
}

export default function Simulate({ userId, onAlert }: SimulateProps) {
  const [simSleep, setSimSleep] = useState(8);
  const [simStress, setSimStress] = useState(3);
  const [simHydration, setSimHydration] = useState(2.5);
  const [simExercise, setSimExercise] = useState(30);
  const [result, setResult] = useState<SimulationResult | null>(null);

  async function handleRun() {
    if (!userId) { onAlert("Connect a user first.", "error"); return; }
    try {
      const data = await runSimulation(userId, {
        sleep_hours: simSleep,
        stress_level: simStress,
        hydration_liters: simHydration,
        exercise_minutes: simExercise,
      });
      setResult(data);
    } catch {
      onAlert("Simulation failed — ensure user is connected.", "error");
    }
  }

  return (
    <div className="card">
      <h2>Counterfactual Simulation</h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1.25rem" }}>
        Ask &ldquo;What if?&rdquo; — modify inputs and see projected vulnerability trajectory over 7 days.
      </p>

      <div className="form-grid">
        <div className="field">
          <label>Hypothetical Sleep Hours</label>
          <div className="range-row">
            <input type="range" min={0} max={12} step={0.5} value={simSleep}
              onChange={(e) => setSimSleep(parseFloat(e.target.value))} />
            <span>{simSleep}</span>
          </div>
        </div>

        <div className="field">
          <label>Hypothetical Stress Level</label>
          <div className="range-row">
            <input type="range" min={0} max={10} step={1} value={simStress}
              onChange={(e) => setSimStress(parseInt(e.target.value))} />
            <span>{simStress}</span>
          </div>
        </div>

        <div className="field">
          <label>Hypothetical Hydration (liters)</label>
          <div className="range-row">
            <input type="range" min={0} max={5} step={0.25} value={simHydration}
              onChange={(e) => setSimHydration(parseFloat(e.target.value))} />
            <span>{simHydration}</span>
          </div>
        </div>

        <div className="field">
          <label>Hypothetical Exercise (min)</label>
          <div className="range-row">
            <input type="range" min={0} max={180} step={5} value={simExercise}
              onChange={(e) => setSimExercise(parseFloat(e.target.value))} />
            <span>{simExercise}</span>
          </div>
        </div>
      </div>

      <button className="primary" onClick={handleRun}>Run Simulation</button>

      {result && (
        <div style={{ marginTop: "1.5rem" }}>
          <h2 style={{ marginBottom: "0.75rem" }}>Projected Trajectory</h2>
          <TrajectoryChart data={result.trajectory ?? []} />
          <div className="grid-3" style={{ marginTop: "1rem" }}>
            <div className="stat">
              <div className="val">{(result.migraine_risk * 100).toFixed(1)}%</div>
              <div className="lbl">Predicted Risk</div>
            </div>
            <div className="stat">
              <div className="val">{(result.uncertainty * 100).toFixed(1)}%</div>
              <div className="lbl">Uncertainty</div>
            </div>
            <div className="stat">
              <div className="val">{(result.trajectory ?? []).length}</div>
              <div className="lbl">Days Simulated</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
