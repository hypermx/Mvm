"""Unit tests for training modules: pretrain, finetune, evaluate."""
from __future__ import annotations

import numpy as np
import pytest
import torch
from torch.utils.data import DataLoader, TensorDataset

from models.foundation.model import NeuralStateSpaceModel
from models.personal.adapter import PersonalAdapter
from training.pretraining.pretrain import pretrain
from training.fine_tuning.finetune import finetune
from training.evaluation.evaluate import evaluate_model, calibration_curve


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_dataloader(
    n_samples: int = 16,
    seq_len: int = 5,
    input_dim: int = 8,
    batch_size: int = 4,
    seed: int = 0,
) -> DataLoader:
    rng = torch.Generator().manual_seed(seed)
    x = torch.rand(n_samples, seq_len, input_dim, generator=rng)
    y = torch.randint(0, 2, (n_samples, seq_len, 1)).float()
    ds = TensorDataset(x, y)
    return DataLoader(ds, batch_size=batch_size)


def _make_tensor_data(
    n_samples: int = 8,
    seq_len: int = 4,
    input_dim: int = 8,
    seed: int = 1,
):
    rng = torch.Generator().manual_seed(seed)
    x = torch.rand(n_samples, seq_len, input_dim, generator=rng)
    y = torch.randint(0, 2, (n_samples, seq_len, 1)).float()
    return x, y


# ---------------------------------------------------------------------------
# pretrain
# ---------------------------------------------------------------------------

class TestPretrain:
    def test_returns_loss_history(self, foundation_model):
        loader = _make_dataloader()
        result = pretrain(foundation_model, loader, epochs=2)
        assert "loss_history" in result
        assert len(result["loss_history"]) == 2

    def test_loss_history_contains_floats(self, foundation_model):
        loader = _make_dataloader()
        result = pretrain(foundation_model, loader, epochs=1)
        assert all(isinstance(v, float) for v in result["loss_history"])

    def test_model_in_eval_mode_after_pretraining(self, foundation_model):
        loader = _make_dataloader()
        pretrain(foundation_model, loader, epochs=1)
        assert not foundation_model.training

    def test_loss_is_positive(self, foundation_model):
        loader = _make_dataloader()
        result = pretrain(foundation_model, loader, epochs=3)
        assert all(v > 0.0 for v in result["loss_history"])

    def test_weights_updated_after_training(self, foundation_model):
        original_weight = foundation_model.encoder_proj.weight.data.clone()
        loader = _make_dataloader()
        pretrain(foundation_model, loader, epochs=5, lr=1e-2)
        assert not torch.allclose(foundation_model.encoder_proj.weight.data, original_weight)


# ---------------------------------------------------------------------------
# finetune
# ---------------------------------------------------------------------------

class TestFinetune:
    def test_returns_loss_history(self, foundation_model, sample_logs):
        adapter = PersonalAdapter(foundation_model, "ft_user")
        result = finetune(adapter, sample_logs, epochs=3)
        assert "loss_history" in result
        assert len(result["loss_history"]) == 3

    def test_adapter_in_eval_mode_after_finetuning(self, foundation_model, sample_logs):
        adapter = PersonalAdapter(foundation_model, "ft_user")
        finetune(adapter, sample_logs, epochs=2)
        assert not adapter.training

    def test_empty_logs_returns_empty_history(self, foundation_model):
        adapter = PersonalAdapter(foundation_model, "ft_user")
        result = finetune(adapter, [], epochs=5)
        assert result == {"loss_history": []}


# ---------------------------------------------------------------------------
# evaluate_model
# ---------------------------------------------------------------------------

class TestEvaluateModel:
    def test_returns_required_keys(self, foundation_model):
        x, y = _make_tensor_data()
        result = evaluate_model(foundation_model, (x, y))
        assert "loss" in result
        assert "accuracy" in result
        assert "auc" in result

    def test_loss_is_non_negative(self, foundation_model):
        x, y = _make_tensor_data()
        result = evaluate_model(foundation_model, (x, y))
        assert result["loss"] >= 0.0

    def test_accuracy_in_unit_interval(self, foundation_model):
        x, y = _make_tensor_data()
        result = evaluate_model(foundation_model, (x, y))
        assert 0.0 <= result["accuracy"] <= 1.0

    def test_accepts_dataloader(self, foundation_model):
        loader = _make_dataloader()
        result = evaluate_model(foundation_model, loader)
        assert "accuracy" in result

    def test_model_in_eval_mode_during_evaluation(self, foundation_model):
        """evaluate_model should not leave model in training mode."""
        x, y = _make_tensor_data()
        evaluate_model(foundation_model, (x, y))
        assert not foundation_model.training


# ---------------------------------------------------------------------------
# calibration_curve
# ---------------------------------------------------------------------------

class TestCalibrationCurve:
    def test_returns_two_arrays(self):
        rng = np.random.default_rng(0)
        y_true = rng.integers(0, 2, size=50).astype(float)
        y_prob = rng.random(50)
        frac_pos, mean_pred = calibration_curve(y_true, y_prob, n_bins=5)
        assert len(frac_pos) > 0
        assert len(mean_pred) > 0
        assert len(frac_pos) == len(mean_pred)

    def test_fraction_of_positives_in_unit_interval(self):
        rng = np.random.default_rng(1)
        y_true = rng.integers(0, 2, size=100).astype(float)
        y_prob = rng.random(100)
        frac_pos, _ = calibration_curve(y_true, y_prob, n_bins=10)
        assert (frac_pos >= 0.0).all() and (frac_pos <= 1.0).all()
