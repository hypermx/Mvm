from __future__ import annotations

import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import numpy as np
import torch
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.data_schema.models import (
    DailyLog,
    InterventionSuggestion,
    SimulationInput,
    UserProfile,
    VulnerabilityState,
)
from backend.ingestion.ingestion import DataIngestionPipeline
from backend.privacy.privacy import PrivacyManager
from models.foundation.model import NeuralStateSpaceModel
from models.personal.adapter import PersonalAdapter
from models.simulation.simulator import CounterfactualSimulator
from models.optimization.policy import InterventionOptimizer

# ---------------------------------------------------------------------------
# In-memory stores (replace with a real DB in production)
# ---------------------------------------------------------------------------
_user_profiles: dict[str, UserProfile] = {}
_user_logs: dict[str, list[DailyLog]] = {}
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
# Users
# ---------------------------------------------------------------------------


@app.post("/users", response_model=UserProfile, status_code=201)
def create_user(profile: UserProfile) -> UserProfile:
    if profile.user_id in _user_profiles:
        raise HTTPException(status_code=409, detail="User already exists")
    _user_profiles[profile.user_id] = profile
    _user_logs.setdefault(profile.user_id, [])
    return profile


@app.get("/users/{user_id}", response_model=UserProfile)
def get_user(user_id: str) -> UserProfile:
    _require_user(user_id)
    return _user_profiles[user_id]


# ---------------------------------------------------------------------------
# Logs
# ---------------------------------------------------------------------------


@app.post("/logs/{user_id}", status_code=201)
def submit_log(user_id: str, log: DailyLog) -> dict[str, Any]:
    _require_user(user_id)
    result = _ingestion.ingest_daily_log(log, user_id)
    _user_logs[user_id].append(log)
    return result


# ---------------------------------------------------------------------------
# Vulnerability
# ---------------------------------------------------------------------------


@app.get("/vulnerability/{user_id}", response_model=VulnerabilityState)
def get_vulnerability(user_id: str) -> VulnerabilityState:
    _require_user(user_id)
    logs = _user_logs.get(user_id, [])
    if not logs:
        # Return a neutral vulnerability when no logs are available.
        return VulnerabilityState(
            user_id=user_id,
            vulnerability_score=0.5,
            confidence=0.0,
        )
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
def run_simulation(user_id: str, payload: SimulationInput) -> dict[str, Any]:
    _require_user(user_id)
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
def get_interventions(user_id: str) -> list[InterventionSuggestion]:
    _require_user(user_id)
    profile = _user_profiles[user_id]
    logs = _user_logs.get(user_id, [])
    suggestions = _optimizer.optimize(
        user_profile=profile,
        current_logs=logs,
        constraints={},
    )
    return suggestions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _require_user(user_id: str) -> None:
    if user_id not in _user_profiles:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
