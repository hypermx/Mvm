"""Tests for Pydantic schema models."""
from __future__ import annotations

from datetime import date

import pytest

from backend.data_schema.models import (
    DailyLog,
    InterventionSuggestion,
    SimulationInput,
    UserProfile,
    VulnerabilityState,
)


class TestDailyLog:
    def test_valid_log(self, sample_log):
        assert sample_log.sleep_hours == 7.0
        assert sample_log.migraine_occurred is False

    def test_migraine_with_intensity(self):
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=6.0,
            sleep_quality=5.0,
            stress_level=7.0,
            hydration_liters=1.5,
            migraine_occurred=True,
            migraine_intensity=6.0,
        )
        assert log.migraine_intensity == 6.0

    def test_intensity_without_migraine_raises(self):
        with pytest.raises(Exception):
            DailyLog(
                date=date(2024, 1, 1),
                sleep_hours=7.0,
                sleep_quality=7.0,
                stress_level=2.0,
                hydration_liters=2.0,
                migraine_occurred=False,
                migraine_intensity=5.0,
            )

    def test_sleep_hours_out_of_range(self):
        with pytest.raises(Exception):
            DailyLog(
                date=date(2024, 1, 1),
                sleep_hours=30.0,
                sleep_quality=5.0,
                stress_level=5.0,
                hydration_liters=2.0,
                migraine_occurred=False,
                migraine_intensity=0.0,
            )

    def test_optional_fields_default_none(self, sample_log):
        assert sample_log.menstrual_cycle_day is None
        assert sample_log.migraine_intensity == 0.0

    def test_no_migraine_with_zero_intensity_valid(self):
        """migraine_occurred=False with intensity == 0 is valid."""
        log = DailyLog(
            date=date(2024, 1, 1),
            sleep_hours=7.0,
            sleep_quality=7.0,
            stress_level=2.0,
            hydration_liters=2.0,
            migraine_occurred=False,
            migraine_intensity=0.0,
        )
        assert log.migraine_intensity == 0.0

    def test_migraine_requires_nonzero_intensity(self):
        """migraine_occurred=True with intensity == 0 is invalid."""
        with pytest.raises(Exception):
            DailyLog(
                date=date(2024, 1, 1),
                sleep_hours=7.0,
                sleep_quality=7.0,
                stress_level=2.0,
                hydration_liters=2.0,
                migraine_occurred=True,
                migraine_intensity=0.0,
            )

    def test_migraine_fields_required(self):
        """Omitting migraine_occurred or migraine_intensity raises."""
        with pytest.raises(Exception):
            DailyLog(
                date=date(2024, 1, 1),
                sleep_hours=7.0,
                sleep_quality=7.0,
                stress_level=2.0,
                hydration_liters=2.0,
            )


class TestUserProfile:
    def test_valid_profile(self, user_profile):
        assert user_profile.personal_threshold == 0.5
        assert user_profile.user_id == "test_user_001"

    def test_invalid_sex(self):
        with pytest.raises(Exception):
            UserProfile(
                user_id="u1",
                age=30,
                sex="alien",
                migraine_history_years=1.0,
                average_migraine_frequency=2.0,
            )

    def test_created_at_auto_set(self, user_profile):
        assert user_profile.created_at is not None


class TestVulnerabilityState:
    def test_valid(self):
        vs = VulnerabilityState(user_id="u1", vulnerability_score=0.7, confidence=0.8)
        assert 0.0 <= vs.vulnerability_score <= 1.0

    def test_score_out_of_range(self):
        with pytest.raises(Exception):
            VulnerabilityState(user_id="u1", vulnerability_score=1.5, confidence=0.5)


class TestSimulationInput:
    def test_valid(self, sample_log):
        si = SimulationInput(
            user_id="u1",
            baseline_logs=[sample_log],
            hypothetical_modifications={"sleep_hours": 9.0},
        )
        assert si.hypothetical_modifications["sleep_hours"] == 9.0


class TestInterventionSuggestion:
    def test_valid(self):
        s = InterventionSuggestion(
            intervention_type="sleep_hours",
            description="Sleep more",
            predicted_risk_reduction=0.2,
            confidence=0.7,
        )
        assert s.predicted_risk_reduction == 0.2
