from __future__ import annotations

from typing import Any

import numpy as np

from backend.data_schema.models import DailyLog, InterventionSuggestion, UserProfile
from backend.ingestion.ingestion import DataIngestionPipeline

_ingestion = DataIngestionPipeline()

# Intervention search space: field → (min_improvement, max_improvement, description_template)
_INTERVENTION_SPACE: dict[str, tuple[float, float, str]] = {
    "sleep_hours": (0.5, 2.0, "Increase sleep by {delta:.1f} hours per night"),
    "sleep_quality": (1.0, 3.0, "Improve sleep quality by {delta:.1f} points (sleep hygiene)"),
    "stress_level": (-3.0, -1.0, "Reduce stress level by {delta:.1f} points (meditation/CBT)"),
    "hydration_liters": (0.5, 1.5, "Increase hydration by {delta:.1f} L per day"),
    "caffeine_mg": (-200.0, -50.0, "Reduce caffeine by {delta:.0f} mg per day"),
    "alcohol_units": (-2.0, -0.5, "Reduce alcohol by {delta:.1f} units per day"),
    "exercise_minutes": (10.0, 40.0, "Increase exercise by {delta:.0f} min per day"),
}


class InterventionOptimizer:
    """Optimizes lifestyle interventions to reduce predicted migraine risk."""

    def optimize(
        self,
        user_profile: UserProfile,
        current_logs: list[DailyLog],
        constraints: dict[str, Any],
    ) -> list[InterventionSuggestion]:
        """Return ranked InterventionSuggestion objects.

        Args:
            user_profile:  The user's profile (threshold, history, etc.).
            current_logs:  Recent daily logs to assess baseline risk.
            constraints:   Optional dict mapping field names to max/min override limits.
        """
        if not current_logs:
            return self._default_suggestions()

        # Compute baseline vulnerability as a simple feature-weighted score.
        baseline_features = np.stack(
            [
                _ingestion.normalize_features(_ingestion.handle_missing_data(lg))
                for lg in current_logs[-14:]
            ]
        )
        baseline_risk = float(np.mean(baseline_features))

        suggestions: list[InterventionSuggestion] = []
        for field, (lo, hi, tmpl) in _INTERVENTION_SPACE.items():
            delta, risk_reduction = self._optimise_field(
                field, lo, hi, baseline_features, constraints
            )
            if risk_reduction <= 0.0:
                continue
            description = tmpl.format(delta=abs(delta))
            confidence = min(0.9, risk_reduction * 1.5 * (len(current_logs) / 30.0 + 0.1))
            suggestions.append(
                InterventionSuggestion(
                    intervention_type=field,
                    description=description,
                    predicted_risk_reduction=round(float(np.clip(risk_reduction, 0.0, 1.0)), 3),
                    confidence=round(float(np.clip(confidence, 0.05, 0.95)), 3),
                    constraints=constraints.get(field, {}),
                )
            )

        # Sort by predicted_risk_reduction descending.
        suggestions.sort(key=lambda s: s.predicted_risk_reduction, reverse=True)
        return suggestions[:5]

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _optimise_field(
        self,
        field: str,
        lo: float,
        hi: float,
        features: np.ndarray,
        constraints: dict[str, Any],
    ) -> tuple[float, float]:
        """Estimate the risk reduction achievable by modifying *field*."""
        # Map field name to feature index.
        from backend.ingestion.ingestion import _FEATURE_RANGES
        keys = list(_FEATURE_RANGES.keys())
        if field not in keys:
            return 0.0, 0.0
        idx = keys.index(field)
        lo_norm, hi_norm = _FEATURE_RANGES[field]

        current_val = float(np.mean(features[:, idx]))
        delta_norm = (hi - lo) / (hi_norm - lo_norm) if hi_norm != lo_norm else 0.0

        # Apply constraint override.
        if field in constraints:
            max_delta = float(constraints[field].get("max_delta", abs(hi - lo)))
            delta_norm = min(abs(delta_norm), max_delta / max(1.0, hi_norm - lo_norm))

        candidate = float(np.clip(current_val + delta_norm * np.sign(hi), 0.0, 1.0))
        risk_reduction = abs(current_val - candidate) * 0.5  # simplified linear model
        return hi, risk_reduction

    def _default_suggestions(self) -> list[InterventionSuggestion]:
        """Return sensible default suggestions when no logs are available."""
        return [
            InterventionSuggestion(
                intervention_type="sleep_hours",
                description="Aim for 7-9 hours of sleep per night",
                predicted_risk_reduction=0.15,
                confidence=0.5,
                constraints={},
            ),
            InterventionSuggestion(
                intervention_type="hydration_liters",
                description="Drink at least 2 L of water per day",
                predicted_risk_reduction=0.10,
                confidence=0.5,
                constraints={},
            ),
        ]
