from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import numpy as np

from backend.data_schema.models import DailyLog

logger = logging.getLogger(__name__)

# Feature columns and their [min, max] normalization ranges.
_FEATURE_RANGES: dict[str, tuple[float, float]] = {
    "sleep_hours": (0.0, 12.0),
    "sleep_quality": (0.0, 10.0),
    "stress_level": (0.0, 10.0),
    "hydration_liters": (0.0, 5.0),
    "caffeine_mg": (0.0, 800.0),
    "alcohol_units": (0.0, 10.0),
    "exercise_minutes": (0.0, 180.0),
    "weather_pressure_hpa": (950.0, 1050.0),
}

# Sensible imputation defaults (population averages).
_DEFAULTS: dict[str, float] = {
    "sleep_hours": 7.5,
    "sleep_quality": 6.0,
    "stress_level": 4.0,
    "hydration_liters": 2.0,
    "caffeine_mg": 100.0,
    "alcohol_units": 0.0,
    "exercise_minutes": 20.0,
    "weather_pressure_hpa": 1013.25,
}


class DataIngestionPipeline:
    """Handles validation, imputation, and normalization of daily health logs."""

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def ingest_daily_log(self, log: DailyLog, user_id: str) -> dict[str, Any]:
        """Full ingestion: handle missing data, validate, normalise.

        Returns a dictionary with the processed log, warnings, and the
        normalised feature vector.
        """
        log = self.handle_missing_data(log)
        warnings = self.validate_log(log)
        features = self.normalize_features(log)
        return {
            "user_id": user_id,
            "date": log.date.isoformat(),
            "processed_log": log.model_dump(),
            "warnings": warnings,
            "normalized_features": features.tolist(),
            "ingested_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate_log(self, log: DailyLog) -> list[str]:
        """Return a list of human-readable warnings about suspicious values."""
        warnings: list[str] = []

        if log.sleep_hours < 4.0:
            warnings.append(f"Very low sleep ({log.sleep_hours:.1f} h). Possible entry error.")
        if log.sleep_hours > 12.0:
            warnings.append(f"Unusually high sleep ({log.sleep_hours:.1f} h).")

        if log.stress_level >= 9.0:
            warnings.append("Extremely high stress recorded (≥9/10).")

        if log.hydration_liters < 0.5:
            warnings.append("Very low hydration (<0.5 L). Check entry.")

        if log.caffeine_mg > 600.0:
            warnings.append(
                f"High caffeine intake ({log.caffeine_mg:.0f} mg). FDA advises <400 mg/day."
            )

        if log.alcohol_units > 6.0:
            warnings.append(f"High alcohol intake ({log.alcohol_units:.1f} units).")

        if log.migraine_occurred and log.migraine_intensity is None:
            warnings.append("Migraine occurred but intensity not recorded.")

        return warnings

    def normalize_features(self, log: DailyLog) -> np.ndarray:
        """Normalize log features to [0, 1] and return a fixed-length vector."""
        values: list[float] = []
        for field, (lo, hi) in _FEATURE_RANGES.items():
            raw = getattr(log, field)
            if raw is None:
                raw = _DEFAULTS[field]
            clipped = float(np.clip(raw, lo, hi))
            values.append((clipped - lo) / (hi - lo) if hi > lo else 0.0)
        return np.array(values, dtype=np.float32)

    def handle_missing_data(self, log: DailyLog) -> DailyLog:
        """Return a copy of *log* with None-valued optional fields imputed."""
        data = log.model_dump()

        if data.get("weather_pressure_hpa") is None:
            data["weather_pressure_hpa"] = _DEFAULTS["weather_pressure_hpa"]

        # menstrual_cycle_day is allowed to remain None (not applicable).
        return DailyLog(**data)
