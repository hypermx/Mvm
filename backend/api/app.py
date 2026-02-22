from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import Any

import numpy as np
import torch
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from backend.data_schema.models import (
    DailyLog,
    InterventionSuggestion,
    SimulationInput,
    UserProfile,
    VulnerabilityState,
)
from backend.db.orm_models import DailyLogORM, UserProfileORM
from backend.db.session import get_db, init_db
from backend.ingestion.ingestion import DataIngestionPipeline
from backend.privacy.privacy import PrivacyManager
from models.foundation.model import NeuralStateSpaceModel
from models.personal.adapter import PersonalAdapter
from models.simulation.simulator import CounterfactualSimulator
from models.optimization.policy import InterventionOptimizer

# ---------------------------------------------------------------------------
# Per-process adapter cache (adapter weights live in memory; user data in DB)
# ---------------------------------------------------------------------------
_adapters: dict[str, PersonalAdapter] = {}

_ingestion = DataIngestionPipeline()
_privacy = PrivacyManager()
_simulator = CounterfactualSimulator()
_optimizer = InterventionOptimizer()

# Shared foundation model (small dims for demo)
_foundation = NeuralStateSpaceModel(input_dim=8, hidden_dim=32, latent_dim=16)


def _get_adapter(user_id: str) -> PersonalAdapter:
    if user_id not in _adapters:
        _adapters[user_id] = PersonalAdapter(base_model=_foundation, user_id=user_id)
    return _adapters[user_id]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Migraine Vulnerability Modeling API",
    version="0.1.0",
    description="REST API for the MVM system",
    lifespan=lifespan,
)

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "")
_allowed_origins = [o.strip() for o in _raw_origins.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_user(user_id: str, db: Session) -> UserProfileORM:
    row = db.get(UserProfileORM, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return row


def _orm_to_profile(row: UserProfileORM) -> UserProfile:
    return UserProfile(
        user_id=row.user_id,
        age=row.age,
        sex=row.sex,
        migraine_history_years=row.migraine_history_years,
        average_migraine_frequency=row.average_migraine_frequency,
        personal_threshold=row.personal_threshold,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _orm_to_log(row: DailyLogORM) -> DailyLog:
    # migraine_intensity may be NULL in rows written before this schema change;
    # default to 0.0 so existing data loads without error.
    intensity = row.migraine_intensity if row.migraine_intensity is not None else 0.0
    occurred = bool(row.migraine_occurred)
    # Legacy rows with occurred=True but NULL intensity: clamp intensity to 1.0
    # so the cross-field invariant (occurred=True => intensity > 0) is satisfied.
    if occurred and intensity == 0.0:
        intensity = 1.0
    return DailyLog(
        date=row.date,
        sleep_hours=row.sleep_hours,
        sleep_quality=row.sleep_quality,
        stress_level=row.stress_level,
        hydration_liters=row.hydration_liters,
        caffeine_mg=row.caffeine_mg,
        alcohol_units=row.alcohol_units,
        exercise_minutes=row.exercise_minutes,
        weather_pressure_hpa=row.weather_pressure_hpa,
        menstrual_cycle_day=row.menstrual_cycle_day,
        migraine_occurred=occurred,
        migraine_intensity=intensity,
    )


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------


@app.post("/users", response_model=UserProfile, status_code=201)
def create_user(profile: UserProfile, db: Session = Depends(get_db)) -> UserProfile:
    if db.get(UserProfileORM, profile.user_id) is not None:
        raise HTTPException(status_code=409, detail="User already exists")
    row = UserProfileORM(
        user_id=profile.user_id,
        age=profile.age,
        sex=profile.sex,
        migraine_history_years=profile.migraine_history_years,
        average_migraine_frequency=profile.average_migraine_frequency,
        personal_threshold=profile.personal_threshold,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _orm_to_profile(row)


@app.get("/users/{user_id}", response_model=UserProfile)
def get_user(user_id: str, db: Session = Depends(get_db)) -> UserProfile:
    row = _require_user(user_id, db)
    return _orm_to_profile(row)


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


@app.post("/logs/{user_id}", status_code=201)
def submit_log(
    user_id: str, log: DailyLog, db: Session = Depends(get_db)
) -> dict[str, Any]:
    _require_user(user_id, db)
    result = _ingestion.ingest_daily_log(log, user_id)
    row = DailyLogORM(
        user_id=user_id,
        date=log.date,
        sleep_hours=log.sleep_hours,
        sleep_quality=log.sleep_quality,
        stress_level=log.stress_level,
        hydration_liters=log.hydration_liters,
        caffeine_mg=log.caffeine_mg,
        alcohol_units=log.alcohol_units,
        exercise_minutes=log.exercise_minutes,
        weather_pressure_hpa=log.weather_pressure_hpa,
        menstrual_cycle_day=log.menstrual_cycle_day,
        migraine_occurred=log.migraine_occurred,
        migraine_intensity=log.migraine_intensity,
    )
    db.add(row)
    db.commit()
    return result


# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------


@app.get("/vulnerability/{user_id}", response_model=VulnerabilityState)
def get_vulnerability(
    user_id: str, db: Session = Depends(get_db)
) -> VulnerabilityState:
    _require_user(user_id, db)
    log_rows = (
        db.query(DailyLogORM)
        .filter(DailyLogORM.user_id == user_id)
        .order_by(DailyLogORM.date)
        .all()
    )
    if not log_rows:
        return VulnerabilityState(
            user_id=user_id,
            vulnerability_score=0.5,
            confidence=0.0,
        )
    logs = [_orm_to_log(r) for r in log_rows]
    adapter = _get_adapter(user_id)
    features = np.stack(
        [_ingestion.normalize_features(_ingestion.handle_missing_data(lg)) for lg in logs[-7:]]
    )
    x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)
    with torch.no_grad():
        _, probs = adapter(x)
    score = float(probs[0, -1].item())
    confidence = min(1.0, len(logs) / 30.0)
    return VulnerabilityState(
        user_id=user_id,
        vulnerability_score=score,
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------


@app.post("/simulate/{user_id}")
def run_simulation(
    user_id: str, payload: SimulationInput, db: Session = Depends(get_db)
) -> dict[str, Any]:
    _require_user(user_id, db)
    adapter = _get_adapter(user_id)
    result = _simulator.simulate(
        baseline_logs=payload.baseline_logs,
        modifications=payload.hypothetical_modifications,
        model=adapter,
    )
    return result


# ---------------------------------------------------------------------------
# Interventions
# ---------------------------------------------------------------------------


@app.get("/interventions/{user_id}", response_model=list[InterventionSuggestion])
def get_interventions(
    user_id: str, db: Session = Depends(get_db)
) -> list[InterventionSuggestion]:
    row = _require_user(user_id, db)
    profile = _orm_to_profile(row)
    log_rows = (
        db.query(DailyLogORM)
        .filter(DailyLogORM.user_id == user_id)
        .order_by(DailyLogORM.date)
        .all()
    )
    logs = [_orm_to_log(r) for r in log_rows]
    suggestions = _optimizer.optimize(
        user_profile=profile,
        current_logs=logs,
        constraints={},
    )
    return suggestions
