"""Tests for the foundation NeuralStateSpaceModel."""
from __future__ import annotations

import torch
import pytest

from models.foundation.model import NeuralStateSpaceModel


class TestNeuralStateSpaceModel:
    def test_forward_output_shapes(self, foundation_model):
        batch, seq_len, input_dim = 2, 10, 8
        x = torch.randn(batch, seq_len, input_dim)
        vuln, probs = foundation_model(x)
        assert vuln.shape == (batch, seq_len, 1)
        assert probs.shape == (batch, seq_len, 1)

    def test_forward_vuln_in_range(self, foundation_model):
        x = torch.randn(1, 5, 8)
        vuln, _ = foundation_model(x)
        assert torch.all(vuln >= 0.0)
        assert torch.all(vuln <= 1.0)

    def test_forward_probs_in_range(self, foundation_model):
        x = torch.randn(1, 5, 8)
        _, probs = foundation_model(x)
        assert torch.all(probs >= 0.0)
        assert torch.all(probs <= 1.0)

    def test_encode_state_shape(self, foundation_model):
        x = torch.randn(3, 7, 8)
        state = foundation_model.encode_state(x)
        assert state.shape == (3, foundation_model.latent_dim)

    def test_parameters_are_learnable(self, foundation_model):
        params = list(foundation_model.parameters())
        assert len(params) > 0

    def test_threshold_parameter_exists(self, foundation_model):
        assert hasattr(foundation_model, "threshold")
        assert isinstance(foundation_model.threshold, torch.nn.Parameter)

    def test_gradient_flows(self, foundation_model):
        x = torch.randn(2, 5, 8)
        y = torch.rand(2, 5, 1)
        _, probs = foundation_model(x)
        loss = torch.nn.functional.binary_cross_entropy(probs, y)
        loss.backward()
        for p in foundation_model.parameters():
            if p.requires_grad and p.grad is not None:
                assert not torch.all(p.grad == 0.0)
                break

    def test_single_step(self, foundation_model):
        x = torch.randn(1, 1, 8)
        vuln, probs = foundation_model(x)
        assert vuln.shape == (1, 1, 1)
        assert probs.shape == (1, 1, 1)
