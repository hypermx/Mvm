from __future__ import annotations

from typing import Any

import numpy as np
import torch
from torch import Tensor

from backend.data_schema.models import DailyLog
from backend.ingestion.ingestion import DataIngestionPipeline

_ingestion = DataIngestionPipeline()


class CounterfactualSimulator:
    """Simulate 'what-if' scenarios by modifying input features."""

    def simulate(
        self,
        baseline_logs: list[DailyLog],
        modifications: dict[str, Any],
        model: Any = None,
        n_steps: int = 7,
    ) -> dict[str, Any]:
        """Run a counterfactual simulation.

        Args:
            baseline_logs:   Historical logs used to build the initial feature matrix.
            modifications:   Dict mapping DailyLog field names → override values applied
                             to all simulation steps.
            model:           A callable ``(x: Tensor) -> (vuln, probs)`` (e.g. PersonalAdapter).
                             If None, a simple linear heuristic is used.
            n_steps:         Number of future steps to simulate.

        Returns:
            Dict with ``trajectory``, ``migraine_risk``, and ``uncertainty``.
        """
        # Build modified feature matrix from baseline logs.
        modified_logs = self._apply_modifications(baseline_logs, modifications)
        recent = modified_logs[-n_steps:] if len(modified_logs) >= n_steps else modified_logs
        features = np.stack(
            [
                _ingestion.normalize_features(_ingestion.handle_missing_data(lg))
                for lg in recent
            ]
        )

        if model is not None:
            trajectories = self._mc_rollout(model, features, n_forward=20)
        else:
            trajectories = self._heuristic_rollout(features, n_forward=20)

        mean_traj = float(np.mean(trajectories, axis=0)[-1])
        trajectory_mean = np.mean(trajectories, axis=0).tolist()
        uncertainty = float(self.compute_uncertainty(trajectories))

        return {
            "trajectory": trajectory_mean,
            "migraine_risk": float(np.clip(mean_traj, 0.0, 1.0)),
            "uncertainty": uncertainty,
        }

    def rollout(self, model: Any, initial_state: Tensor, input_sequence: Tensor) -> Tensor:
        """Run the model on *input_sequence* and return migraine probability trajectory."""
        with torch.no_grad():
            _, probs = model(input_sequence)
        return probs.squeeze(0).squeeze(-1)  # (T,)

    def compute_uncertainty(self, trajectories: list[list[float]] | np.ndarray) -> float:
        """Compute MC-dropout uncertainty as mean standard deviation across trajectories."""
        arr = np.array(trajectories)  # (n_forward, T)
        return float(np.mean(np.std(arr, axis=0)))

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _apply_modifications(
        self, logs: list[DailyLog], modifications: dict[str, Any]
    ) -> list[DailyLog]:
        if not modifications:
            return logs
        modified: list[DailyLog] = []
        for log in logs:
            data = log.model_dump()
            data.update(modifications)
            modified.append(DailyLog(**data))
        return modified

    def _mc_rollout(
        self, model: Any, features: np.ndarray, n_forward: int
    ) -> list[list[float]]:
        """Monte Carlo dropout rollout; enables dropout during inference."""
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)  # (1, T, F)
        trajectories: list[list[float]] = []
        model.train()  # activate dropout
        with torch.no_grad():
            for _ in range(n_forward):
                _, probs = model(x)
                traj = probs.squeeze(0).squeeze(-1).cpu().numpy().tolist()
                trajectories.append(traj)
        model.eval()
        return trajectories

    def _heuristic_rollout(
        self, features: np.ndarray, n_forward: int
    ) -> list[list[float]]:
        """Simple weighted-average heuristic when no model is provided."""
        weights = np.array([0.3, 0.2, 0.15, 0.1, 0.1, 0.05, 0.05, 0.05])
        w = weights[: features.shape[1]]
        w = w / w.sum()
        base_score = float(np.mean(features @ w))
        rng = np.random.default_rng(42)
        trajectories = [
            [float(np.clip(base_score + rng.normal(0, 0.05), 0.0, 1.0)) for _ in range(len(features))]
            for _ in range(n_forward)
        ]
        return trajectories
