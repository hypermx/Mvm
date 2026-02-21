"""Tests for baseline models."""
from __future__ import annotations

import numpy as np
import pytest

from models.baseline import BaselineModels


@pytest.fixture()
def fitted_model(random_features, random_labels) -> BaselineModels:
    model = BaselineModels()
    model.fit(random_features, random_labels)
    return model


class TestBaselineModels:
    def test_predict_proba_shape(self, fitted_model, random_features):
        proba = fitted_model.predict_proba(random_features)
        assert proba.shape == (len(random_features), 2)

    def test_predict_proba_sums_to_one(self, fitted_model, random_features):
        proba = fitted_model.predict_proba(random_features)
        np.testing.assert_allclose(proba.sum(axis=1), 1.0, atol=1e-5)

    def test_predict_proba_in_range(self, fitted_model, random_features):
        proba = fitted_model.predict_proba(random_features)
        assert np.all(proba >= 0.0)
        assert np.all(proba <= 1.0)

    def test_evaluate_returns_expected_keys(self, fitted_model, random_features, random_labels):
        metrics = fitted_model.evaluate(random_features, random_labels)
        assert "accuracy" in metrics
        assert "auc" in metrics
        assert "brier_score" in metrics
        assert "calibration_error" in metrics

    def test_evaluate_accuracy_range(self, fitted_model, random_features, random_labels):
        metrics = fitted_model.evaluate(random_features, random_labels)
        assert 0.0 <= metrics["accuracy"] <= 1.0

    def test_unfitted_model_raises(self, random_features):
        model = BaselineModels()
        with pytest.raises(RuntimeError):
            model.predict_proba(random_features)

    def test_fit_returns_self(self, random_features, random_labels):
        model = BaselineModels()
        result = model.fit(random_features, random_labels)
        assert result is model
