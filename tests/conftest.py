"""Shared pytest fixtures for MVM tests."""
from __future__ import annotations

from datetime import date

import numpy as np
import pytest
import torch

from backend.data_schema.models import DailyLog, UserProfile
from models.foundation.model import NeuralStateSpaceModel


@pytest.fixture()
def sample_log() -> DailyLog:
    return DailyLog(
        date=date(2024, 1, 15),
        sleep_hours=7.0,
        sleep_quality=6.5,
        stress_level=4.0,
        hydration_liters=2.0,
        caffeine_mg=100.0,
        alcohol_units=0.0,
        exercise_minutes=30.0,
        weather_pressure_hpa=1013.0,
        migraine_occurred=False,
    )


@pytest.fixture()
def migraine_log() -> DailyLog:
    return DailyLog(
        date=date(2024, 1, 16),
        sleep_hours=5.0,
        sleep_quality=3.0,
        stress_level=8.0,
        hydration_liters=1.0,
        caffeine_mg=300.0,
        alcohol_units=2.0,
        exercise_minutes=0.0,
        weather_pressure_hpa=995.0,
        migraine_occurred=True,
        migraine_intensity=7.0,
    )


@pytest.fixture()
def sample_logs(sample_log, migraine_log) -> list[DailyLog]:
    logs = []
    for i in range(14):
        base = migraine_log if i % 7 == 6 else sample_log
        data = base.model_dump()
        from datetime import timedelta
        data["date"] = date(2024, 1, 1) + timedelta(days=i)
        logs.append(DailyLog(**data))
    return logs


@pytest.fixture()
def user_profile() -> UserProfile:
    return UserProfile(
        user_id="test_user_001",
        age=35,
        sex="female",
        migraine_history_years=5.0,
        average_migraine_frequency=3.0,
    )


@pytest.fixture()
def foundation_model() -> NeuralStateSpaceModel:
    return NeuralStateSpaceModel(input_dim=8, hidden_dim=16, latent_dim=8)


@pytest.fixture()
def random_features() -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.random((20, 8)).astype(np.float32)


@pytest.fixture()
def random_labels(random_features) -> np.ndarray:
    rng = np.random.default_rng(42)
    return rng.integers(0, 2, size=20).astype(np.float32)
