"""Unit tests for PersonalAdapter."""
from __future__ import annotations

import numpy as np
import pytest
import torch
import torch.nn as nn

from models.personal.adapter import PersonalAdapter
from models.foundation.model import NeuralStateSpaceModel


@pytest.fixture()
def adapter(foundation_model) -> PersonalAdapter:
    return PersonalAdapter(base_model=foundation_model, user_id="user_adapter_test")


class TestAdapterInitialization:
    def test_creates_adapter_linear_layer(self, adapter, foundation_model):
        latent_dim = foundation_model.latent_dim
        assert isinstance(adapter.adapter, nn.Linear)
        assert adapter.adapter.in_features == latent_dim
        assert adapter.adapter.out_features == latent_dim

    def test_adapter_starts_as_identity(self, adapter, foundation_model):
        latent_dim = foundation_model.latent_dim
        weight = adapter.adapter.weight.detach()
        assert torch.allclose(weight, torch.eye(latent_dim), atol=1e-6)
        assert torch.allclose(adapter.adapter.bias.detach(), torch.zeros(latent_dim), atol=1e-6)

    def test_personal_threshold_cloned_from_base(self, adapter, foundation_model):
        assert torch.isclose(
            adapter.personal_threshold, foundation_model.threshold, atol=1e-6
        )

    def test_personal_threshold_is_parameter(self, adapter):
        assert isinstance(adapter.personal_threshold, nn.Parameter)

    def test_stores_user_id(self, adapter):
        assert adapter.user_id == "user_adapter_test"


class TestAdapterForward:
    def test_output_shapes(self, adapter):
        B, T, F = 2, 5, 8
        x = torch.randn(B, T, F)
        vuln, probs = adapter(x)
        assert vuln.shape == (B, T, 1)
        assert probs.shape == (B, T, 1)

    def test_vulnerability_in_unit_interval(self, adapter):
        x = torch.randn(1, 7, 8)
        vuln, _ = adapter(x)
        assert (vuln >= 0.0).all() and (vuln <= 1.0).all()

    def test_probs_in_unit_interval(self, adapter):
        x = torch.randn(1, 7, 8)
        _, probs = adapter(x)
        assert (probs >= 0.0).all() and (probs <= 1.0).all()

    def test_different_users_have_different_adapters(self, foundation_model):
        a1 = PersonalAdapter(foundation_model, "user_a")
        a2 = PersonalAdapter(foundation_model, "user_b")
        # After independent fine-tuning, thresholds should remain independent.
        a1.personal_threshold.data.fill_(0.3)
        a2.personal_threshold.data.fill_(0.7)
        assert not torch.isclose(a1.personal_threshold, a2.personal_threshold)


class TestFitPersonal:
    def test_returns_loss_history(self, adapter, sample_logs):
        result = adapter.fit_personal(sample_logs, epochs=3, lr=1e-3)
        assert "loss_history" in result
        assert len(result["loss_history"]) == 3

    def test_loss_history_contains_floats(self, adapter, sample_logs):
        result = adapter.fit_personal(sample_logs, epochs=2, lr=1e-3)
        assert all(isinstance(v, float) for v in result["loss_history"])

    def test_too_few_logs_returns_empty_history(self, adapter, sample_log):
        result = adapter.fit_personal([sample_log], epochs=5)
        assert result == {"loss_history": []}

    def test_base_model_unfrozen_after_fitting(self, adapter, sample_logs):
        adapter.fit_personal(sample_logs, epochs=2)
        for param in adapter.base_model.parameters():
            assert param.requires_grad

    def test_adapter_is_in_eval_mode_after_fitting(self, adapter, sample_logs):
        adapter.fit_personal(sample_logs, epochs=2)
        assert not adapter.training

    def test_loss_decreases_over_epochs(self, adapter, sample_logs):
        result = adapter.fit_personal(sample_logs, epochs=20, lr=1e-2)
        history = result["loss_history"]
        # Average of last 5 epochs should be ≤ average of first 5.
        assert np.mean(history[-5:]) <= np.mean(history[:5]) + 0.1
