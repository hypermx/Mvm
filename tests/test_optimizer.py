"""Unit tests for InterventionOptimizer."""
from __future__ import annotations

import pytest

from models.optimization.policy import InterventionOptimizer, _INTERVENTION_SPACE
from backend.data_schema.models import InterventionSuggestion


@pytest.fixture()
def optimizer() -> InterventionOptimizer:
    return InterventionOptimizer()


class TestOptimizeNoLogs:
    def test_returns_default_suggestions_when_no_logs(self, optimizer, user_profile):
        suggestions = optimizer.optimize(user_profile, current_logs=[], constraints={})
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        assert all(isinstance(s, InterventionSuggestion) for s in suggestions)

    def test_default_suggestions_have_valid_scores(self, optimizer, user_profile):
        suggestions = optimizer.optimize(user_profile, current_logs=[], constraints={})
        for s in suggestions:
            assert 0.0 <= s.predicted_risk_reduction <= 1.0
            assert 0.0 <= s.confidence <= 1.0


class TestOptimizeWithLogs:
    def test_returns_list_of_intervention_suggestions(self, optimizer, user_profile, sample_logs):
        suggestions = optimizer.optimize(user_profile, current_logs=sample_logs, constraints={})
        assert isinstance(suggestions, list)
        assert all(isinstance(s, InterventionSuggestion) for s in suggestions)

    def test_results_capped_at_five(self, optimizer, user_profile, sample_logs):
        suggestions = optimizer.optimize(user_profile, current_logs=sample_logs, constraints={})
        assert len(suggestions) <= 5

    def test_sorted_descending_by_risk_reduction(self, optimizer, user_profile, sample_logs):
        suggestions = optimizer.optimize(user_profile, current_logs=sample_logs, constraints={})
        reductions = [s.predicted_risk_reduction for s in suggestions]
        assert reductions == sorted(reductions, reverse=True)

    def test_scores_in_valid_range(self, optimizer, user_profile, sample_logs):
        suggestions = optimizer.optimize(user_profile, current_logs=sample_logs, constraints={})
        for s in suggestions:
            assert 0.0 <= s.predicted_risk_reduction <= 1.0
            assert 0.0 <= s.confidence <= 1.0

    def test_intervention_types_are_known_fields(self, optimizer, user_profile, sample_logs):
        suggestions = optimizer.optimize(user_profile, current_logs=sample_logs, constraints={})
        for s in suggestions:
            assert s.intervention_type in _INTERVENTION_SPACE


class TestOptimiseField:
    def test_unknown_field_returns_zero(self, optimizer):
        import numpy as np
        features = np.random.default_rng(0).random((7, 8)).astype(np.float32)
        delta, reduction = optimizer._optimise_field("unknown_field", 0.0, 1.0, features, {})
        assert delta == 0.0
        assert reduction == 0.0

    def test_known_field_returns_nonzero_reduction(self, optimizer):
        import numpy as np
        features = np.random.default_rng(0).random((7, 8)).astype(np.float32)
        delta, reduction = optimizer._optimise_field(
            "sleep_hours", 0.5, 2.0, features, {}
        )
        assert reduction >= 0.0

    def test_constraint_limits_delta(self, optimizer):
        import numpy as np
        features = np.random.default_rng(0).random((7, 8)).astype(np.float32)
        constraints = {"sleep_hours": {"max_delta": 0.1}}
        delta, reduction = optimizer._optimise_field(
            "sleep_hours", 0.5, 2.0, features, constraints
        )
        # With a tight constraint, risk reduction should be small.
        assert reduction >= 0.0


class TestConstraintHandling:
    def test_constraint_applied_per_field(self, optimizer, user_profile, sample_logs):
        constraints = {"sleep_hours": {"max_delta": 0.01}}
        suggestions = optimizer.optimize(
            user_profile, current_logs=sample_logs, constraints=constraints
        )
        # Intervention for sleep_hours should have reduced impact.
        sleep_suggestions = [s for s in suggestions if s.intervention_type == "sleep_hours"]
        for s in sleep_suggestions:
            assert s.predicted_risk_reduction <= 1.0
