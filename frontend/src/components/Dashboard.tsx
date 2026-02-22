"use client";

import { useState, useCallback } from "react";
import TrajectoryChart from "./TrajectoryChart";
import { getVulnerability, VulnerabilityResponse } from "@/lib/api";

interface DashboardProps {
  userId: string;
  logCount: number;
  onAlert: (msg: string, type?: "success" | "error") => void;
}

function generateDemoTrajectory(current: number): number[] {
  const pts: number[] = [];
  let v = Math.max(0, current - 0.3 + Math.random() * 0.2);
  for (let i = 0; i < 6; i++) {
    v = Math.min(1, Math.max(0, v + (Math.random() - 0.45) * 0.12));
    pts.push(v);
  }
  pts.push(current);
  return pts;
}

function riskColor(score: number): string {
  return score >= 0.7 ? "var(--danger)" : score >= 0.4 ? "#facc15" : "var(--accent2)";
}

function riskLabel(score: number): string {
  return score >= 0.7 ? "High" : score >= 0.4 ? "Med" : "Low";
}

export default function Dashboard({ userId, logCount, onAlert }: DashboardProps) {
  const [vuln, setVuln] = useState<VulnerabilityResponse | null>(null);
  const [trajectory, setTrajectory] = useState<number[]>([]);

  const refresh = useCallback(async () => {
    if (!userId) { onAlert("Connect a user first.", "error"); return; }
    try {
      const data = await getVulnerability(userId);
      setVuln(data);
      setTrajectory(generateDemoTrajectory(data.vulnerability_score));
    } catch {
      onAlert("Could not fetch vulnerability — connect a user first.", "error");
    }
  }, [userId, onAlert]);

  const gaugeColor = vuln
    ? vuln.vulnerability_score >= 0.7
      ? "#ff6b6b"
      : vuln.vulnerability_score >= 0.4
      ? "#facc15"
      : "#4ecdc4"
    : "#7c6af7";

  const gaugePct = vuln ? Math.min(Math.max(vuln.vulnerability_score, 0), 1) : 0;
  const totalDash = 220;
  const dashOffset = totalDash * (1 - gaugePct);

  return (
    <>
      <div className="grid-2">
        <div className="card">
          <h2>Current Vulnerability</h2>
          <div className="gauge-wrap">
            <div className="gauge">
              <svg viewBox="0 0 160 80">
                <path
                  d="M10 75 A70 70 0 0 1 150 75"
                  fill="none"
                  stroke="#2d3148"
                  strokeWidth="12"
                  strokeLinecap="round"
                />
                <path
                  d="M10 75 A70 70 0 0 1 150 75"
                  fill="none"
                  stroke={gaugeColor}
                  strokeWidth="12"
                  strokeLinecap="round"
                  strokeDasharray={totalDash}
                  strokeDashoffset={dashOffset}
                />
              </svg>
            </div>
            <div className="gauge-value">
              {vuln ? `${(gaugePct * 100).toFixed(0)}%` : "—"}
            </div>
            <div className="gauge-label">
              {vuln && vuln.confidence > 0
                ? `Confidence: ${(vuln.confidence * 100).toFixed(0)}%`
                : "No data yet"}
            </div>
            <button className="primary" style={{ marginTop: "0.5rem" }} onClick={refresh}>
              Refresh
            </button>
          </div>
        </div>

        <div className="card">
          <h2>7-Day Trajectory</h2>
          <TrajectoryChart data={trajectory} />
        </div>
      </div>

      <div className="card">
        <h2>Quick Stats</h2>
        <div className="grid-3">
          <div className="stat">
            <div className="val">{logCount}</div>
            <div className="lbl">Logs Submitted</div>
          </div>
          <div className="stat">
            <div className="val">
              {vuln ? `${(vuln.confidence * 100).toFixed(0)}%` : "—"}
            </div>
            <div className="lbl">Model Confidence</div>
          </div>
          <div className="stat">
            <div
              className="val"
              style={{ color: vuln ? riskColor(vuln.vulnerability_score) : undefined }}
            >
              {vuln ? riskLabel(vuln.vulnerability_score) : "—"}
            </div>
            <div className="lbl">Risk Level</div>
          </div>
        </div>
      </div>
    </>
  );
}
