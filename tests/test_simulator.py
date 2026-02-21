"""Unit tests for CounterfactualSimulator."""
from __future__ import annotations

import numpy as np
import pytest
import torch

from models.simulation.simulator import CounterfactualSimulator


@pytest.fixture()
def simulator() -> CounterfactualSimulator:
    return CounterfactualSimulator()


class TestComputeUncertainty:
    def test_identical_trajectories_have_zero_uncertainty(self, simulator):
        trajectories = [[0.4, 0.5, 0.6]] * 10
        assert simulator.compute_uncertainty(trajectories) == pytest.approx(0.0)

    def test_varied_trajectories_have_positive_uncertainty(self, simulator):
        rng = np.random.default_rng(0)
        trajectories = rng.random((20, 5)).tolist()
        assert simulator.compute_uncertainty(trajectories) > 0.0

    def test_single_trajectory_has_zero_uncertainty(self, simulator):
        trajectories = [[0.3, 0.7, 0.5]]
        assert simulator.compute_uncertainty(trajectories) == pytest.approx(0.0)

    def test_accepts_numpy_array(self, simulator):
        arr = np.array([[0.1, 0.9], [0.9, 0.1]])
        uncertainty = simulator.compute_uncertainty(arr)
        assert uncertainty > 0.0


class TestHeuristicRollout:
    def test_returns_correct_shape(self, simulator, sample_logs):
        features = np.random.default_rng(0).random((5, 8)).astype(np.float32)
        trajectories = simulator._heuristic_rollout(features, n_forward=10)
        assert len(trajectories) == 10
        assert all(len(t) == 5 for t in trajectories)

    def test_values_are_clipped_to_unit_interval(self, simulator):
        features = np.ones((7, 8), dtype=np.float32)
        trajectories = simulator._heuristic_rollout(features, n_forward=15)
        for traj in trajectories:
            for v in traj:
                assert 0.0 <= v <= 1.0

    def test_is_deterministic_with_same_seed(self, simulator):
        features = np.random.default_rng(1).random((5, 8)).astype(np.float32)
        t1 = simulator._heuristic_rollout(features, n_forward=5)
        t2 = simulator._heuristic_rollout(features, n_forward=5)
        assert t1 == t2


class TestMCRollout:
    def test_returns_correct_shape(self, simulator, foundation_model):
        foundation_model.eval()
        features = np.random.default_rng(0).random((4, 8)).astype(np.float32)
        trajectories = simulator._mc_rollout(foundation_model, features, n_forward=5)
        assert len(trajectories) == 5
        assert all(len(t) == 4 for t in trajectories)

    def test_model_restored_to_eval_after_rollout(self, simulator, foundation_model):
        foundation_model.eval()
        features = np.random.default_rng(0).random((3, 8)).astype(np.float32)
        simulator._mc_rollout(foundation_model, features, n_forward=3)
        assert not foundation_model.training

    def test_produces_varied_trajectories_with_dropout(self, simulator, foundation_model):
        """With dropout enabled (train mode), consecutive rollouts should differ."""
        features = np.random.default_rng(42).random((5, 8)).astype(np.float32)
        trajectories = simulator._mc_rollout(foundation_model, features, n_forward=20)
        # At least some trajectories should differ due to MC-dropout.
        unique = {tuple(t) for t in trajectories}
        assert len(unique) > 1


class TestSimulate:
    def test_simulate_without_model(self, simulator, sample_logs):
        result = simulator.simulate(
            baseline_logs=sample_logs,
            modifications={"sleep_hours": 9.0},
            model=None,
            n_steps=7,
        )
        assert "trajectory" in result
        assert "migraine_risk" in result
        assert "uncertainty" in result
        assert 0.0 <= result["migraine_risk"] <= 1.0
        assert result["uncertainty"] >= 0.0

    def test_simulate_with_model(self, simulator, sample_logs, foundation_model):
        result = simulator.simulate(
            baseline_logs=sample_logs,
            modifications={},
            model=foundation_model,
            n_steps=5,
        )
        assert "trajectory" in result
        assert 0.0 <= result["migraine_risk"] <= 1.0

    def test_simulate_no_modifications(self, simulator, sample_logs):
        result = simulator.simulate(
            baseline_logs=sample_logs,
            modifications={},
            model=None,
        )
        assert isinstance(result["trajectory"], list)

    def test_simulate_single_log(self, simulator, sample_log):
        result = simulator.simulate(
            baseline_logs=[sample_log],
            modifications={"stress_level": 1.0},
            model=None,
            n_steps=1,
        )
        assert "migraine_risk" in result
