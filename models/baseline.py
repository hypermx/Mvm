from __future__ import annotations

import numpy as np
from sklearn.calibration import calibration_curve as sklearn_calibration_curve
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, roc_auc_score, accuracy_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler


class BaselineModels:
    """Logistic regression and gradient boosting wrappers for migraine prediction."""

    def __init__(self) -> None:
        self._lr = Pipeline(
            [
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, C=1.0)),
            ]
        )
        self._gb = GradientBoostingClassifier(n_estimators=100, max_depth=3, learning_rate=0.1)
        self._fitted = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def fit(self, X: np.ndarray, y: np.ndarray) -> "BaselineModels":
        """Fit both baseline models on *(X, y)*."""
        self._lr.fit(X, y)
        self._gb.fit(X, y)
        self._fitted = True
        return self

    # ------------------------------------------------------------------
    # Inference
    # ------------------------------------------------------------------

    def predict_proba(self, X: np.ndarray) -> np.ndarray:
        """Return average predicted probability from both models (shape: ``[n, 2]``)."""
        self._check_fitted()
        lr_prob = self._lr.predict_proba(X)
        gb_prob = self._gb.predict_proba(X)
        return (lr_prob + gb_prob) / 2.0

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(self, X: np.ndarray, y: np.ndarray) -> dict[str, float]:
        """Return accuracy, AUC, Brier score, and calibration error."""
        self._check_fitted()
        proba = self.predict_proba(X)[:, 1]
        preds = (proba >= 0.5).astype(int)

        fraction_of_positives, mean_predicted = sklearn_calibration_curve(
            y, proba, n_bins=min(10, max(2, int(np.sum(y))))
        )
        calibration_error = float(np.mean(np.abs(fraction_of_positives - mean_predicted)))

        return {
            "accuracy": float(accuracy_score(y, preds)),
            "auc": float(roc_auc_score(y, proba)) if len(np.unique(y)) > 1 else 0.0,
            "brier_score": float(brier_score_loss(y, proba)),
            "calibration_error": calibration_error,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_fitted(self) -> None:
        if not self._fitted:
            raise RuntimeError("Call fit() before predict_proba() or evaluate().")
