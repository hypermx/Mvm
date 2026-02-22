from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class DailyLog(BaseModel):
    """Daily health log submitted by a user.

    Migraine semantics:
    - Both ``migraine_occurred`` and ``migraine_intensity`` are **required**.
    - If no migraine happened, supply ``migraine_occurred=False`` and
      ``migraine_intensity=0``.
    - If a migraine happened, supply ``migraine_occurred=True`` and an
      intensity in the range (0, 10].
    - ``migraine_occurred=False`` with ``migraine_intensity > 0`` is invalid.
    - ``migraine_occurred=True`` with ``migraine_intensity == 0`` is invalid.
    """

    date: date
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    sleep_quality: float = Field(..., ge=0.0, le=10.0)
    stress_level: float = Field(..., ge=0.0, le=10.0)
    hydration_liters: float = Field(..., ge=0.0, le=20.0)
    caffeine_mg: float = Field(default=0.0, ge=0.0)
    alcohol_units: float = Field(default=0.0, ge=0.0)
    exercise_minutes: float = Field(default=0.0, ge=0.0)
    weather_pressure_hpa: Optional[float] = Field(default=None, ge=800.0, le=1100.0)
    menstrual_cycle_day: Optional[int] = Field(default=None, ge=1, le=35)
    migraine_occurred: bool
    migraine_intensity: float = Field(..., ge=0.0, le=10.0)

    @model_validator(mode="after")
    def validate_migraine_consistency(self) -> "DailyLog":
        """Enforce that intensity and occurrence are mutually consistent.

        - ``migraine_occurred=False`` requires ``migraine_intensity == 0``.
        - ``migraine_occurred=True`` requires ``migraine_intensity > 0``.
        """
        # Use a small tolerance to avoid floating-point precision pitfalls.
        intensity_is_zero = self.migraine_intensity < 1e-9
        if not self.migraine_occurred and not intensity_is_zero:
            raise ValueError(
                "migraine_intensity must be 0 when migraine_occurred is False"
            )
        if self.migraine_occurred and intensity_is_zero:
            raise ValueError(
                "migraine_intensity must be > 0 when migraine_occurred is True"
            )
        return self


class UserProfile(BaseModel):
    """Per-user profile and preferences."""

    user_id: str
    age: int = Field(..., ge=0, le=120)
    sex: str = Field(..., pattern="^(male|female|other)$")
    migraine_history_years: float = Field(..., ge=0.0)
    average_migraine_frequency: float = Field(..., ge=0.0, description="Migraines per month")
    personal_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserProfileUpdate(BaseModel):
    """Partial update for a user profile."""

    age: Optional[int] = Field(default=None, ge=0, le=120)
    sex: Optional[str] = Field(default=None, pattern="^(male|female|other)$")
    migraine_history_years: Optional[float] = Field(default=None, ge=0.0)
    average_migraine_frequency: Optional[float] = Field(
        default=None, ge=0.0, description="Migraines per month"
    )
    personal_threshold: Optional[float] = Field(default=None, ge=0.0, le=1.0)


class VulnerabilityState(BaseModel):
    """Snapshot of a user's current vulnerability score."""

    user_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    vulnerability_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)


class SimulationInput(BaseModel):
    """Input for a counterfactual simulation."""

    user_id: str
    baseline_logs: list[DailyLog]
    hypothetical_modifications: dict = Field(
        default_factory=dict,
        description=(
            "Keys are DailyLog field names, values are the modified values "
            "to apply uniformly across all simulation steps."
        ),
    )


class InterventionSuggestion(BaseModel):
    """A ranked recommendation to reduce migraine risk."""

    intervention_type: str
    description: str
    predicted_risk_reduction: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    constraints: dict = Field(default_factory=dict)
