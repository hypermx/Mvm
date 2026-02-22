"use client";

import { useState } from "react";
import { getInterventions, Intervention } from "@/lib/api";

interface InterventionsProps {
  userId: string;
  onAlert: (msg: string, type?: "success" | "error") => void;
}

export default function Interventions({ userId, onAlert }: InterventionsProps) {
  const [items, setItems] = useState<Intervention[]>([]);
  const [loaded, setLoaded] = useState(false);

  async function load() {
    if (!userId) { onAlert("Connect a user first.", "error"); return; }
    try {
      const data = await getInterventions(userId);
      setItems(data);
      setLoaded(true);
    } catch {
      onAlert("Could not load interventions.", "error");
    }
  }

  return (
    <div className="card">
      <h2>Intervention Suggestions</h2>
      <p style={{ color: "var(--text-muted)", fontSize: "0.875rem", marginBottom: "1.25rem" }}>
        Evidence-based, personalised suggestions ranked by predicted risk reduction.
      </p>
      <button className="primary" onClick={load}>Get Suggestions</button>

      <div style={{ marginTop: "1.25rem" }}>
        {loaded && items.length === 0 && (
          <p style={{ color: "var(--text-muted)" }}>
            No suggestions yet — add some daily logs first.
          </p>
        )}
        {items.map((item, idx) => {
          const pct = Math.round(item.predicted_risk_reduction * 100);
          const cls = pct >= 20 ? "green" : pct >= 10 ? "yellow" : "red";
          return (
            <div key={idx} className="intervention">
              <div className="details">
                <div className="type">{item.intervention_type}</div>
                <div className="desc">{item.description}</div>
              </div>
              <span className={`badge ${cls}`}>−{pct}% risk</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
