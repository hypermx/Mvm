export const API = "/api";

/** Default values applied to new user profiles at registration time. */
export const NEW_USER_DEFAULTS = {
  age: 30,
  sex: "other",
  migraine_history_years: 0,
  average_migraine_frequency: 0,
} as const;

export interface VulnerabilityResponse {
  vulnerability_score: number;
  confidence: number;
}

export interface DailyLog {
  date: string;
  sleep_hours: number;
  sleep_quality: number;
  stress_level: number;
  hydration_liters: number;
  caffeine_mg: number;
  alcohol_units: number;
  exercise_minutes: number;
  weather_pressure_hpa: number;
  migraine_occurred: boolean;
  migraine_intensity: number | null;
}

export interface SimulationResult {
  migraine_risk: number;
  uncertainty: number;
  trajectory: number[];
}

export interface Intervention {
  intervention_type: string;
  description: string;
  predicted_risk_reduction: number;
}

export interface UserProfile {
  user_id: string;
  age: number;
  sex: string;
  migraine_history_years: number;
  average_migraine_frequency: number;
  personal_threshold: number;
}

export interface UserProfileUpdate {
  age?: number;
  sex?: string;
  migraine_history_years?: number;
  average_migraine_frequency?: number;
  personal_threshold?: number;
}

export async function getUser(userId: string): Promise<Response> {
  return fetch(`${API}/users/${userId}`);
}

export async function createUser(userId: string): Promise<Response> {
  return fetch(`${API}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_id: userId,
      age: NEW_USER_DEFAULTS.age,
      sex: NEW_USER_DEFAULTS.sex,
      migraine_history_years: NEW_USER_DEFAULTS.migraine_history_years,
      average_migraine_frequency: NEW_USER_DEFAULTS.average_migraine_frequency,
    }),
  });
}

export async function updateUser(
  userId: string,
  update: UserProfileUpdate
): Promise<UserProfile> {
  const res = await fetch(`${API}/users/${userId}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(update),
  });
  if (!res.ok) throw new Error("Could not update user profile");
  return res.json();
}

export async function getVulnerability(
  userId: string
): Promise<VulnerabilityResponse> {
  const res = await fetch(`${API}/vulnerability/${userId}`);
  if (!res.ok) throw new Error("Could not fetch vulnerability");
  return res.json();
}

export async function submitLog(
  userId: string,
  log: DailyLog
): Promise<Response> {
  return fetch(`${API}/logs/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(log),
  });
}

export async function runSimulation(
  userId: string,
  modifications: Partial<DailyLog>
): Promise<SimulationResult> {
  const res = await fetch(`${API}/simulate/${userId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      baseline_logs: [],
      hypothetical_modifications: modifications,
    }),
  });
  if (!res.ok) throw new Error("Simulation failed");
  return res.json();
}

export async function getInterventions(
  userId: string
): Promise<Intervention[]> {
  const res = await fetch(`${API}/interventions/${userId}`);
  if (!res.ok) throw new Error("Could not load interventions");
  return res.json();
}
