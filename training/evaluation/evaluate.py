from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import torch
from torch import Tensor

try:
    import matplotlib.pyplot as plt
    _HAS_MPL = True
except ImportError:
    _HAS_MPL = False


def evaluate_model(model: Any, test_data: Any) -> dict[str, float]:
    """Evaluate *model* on *test_data*.

    *test_data* may be:
    - A tuple ``(x_tensor, y_tensor)``
    - A ``DataLoader`` yielding ``(x, y)`` batches

    Returns:
        Dict with ``loss``, ``accuracy``, and ``auc``.
    """
    from sklearn.metrics import accuracy_score, roc_auc_score
    criterion = torch.nn.BCELoss()

    all_probs: list[float] = []
    all_labels: list[float] = []
    total_loss = 0.0
    n_batches = 0

    model.eval()
    with torch.no_grad():
        if isinstance(test_data, tuple):
            batches = [test_data]
        else:
            batches = list(test_data)

        for x, y in batches:
            x = x.float()
            y = y.float()
            _, probs = model(x)
            loss = criterion(probs, y)
            total_loss += float(loss.item())
            n_batches += 1
            all_probs.extend(probs.flatten().cpu().numpy().tolist())
            all_labels.extend(y.flatten().cpu().numpy().tolist())

    all_probs_arr = np.array(all_probs)
    all_labels_arr = np.array(all_labels)
    preds = (all_probs_arr >= 0.5).astype(int)

    return {
        "loss": total_loss / max(n_batches, 1),
        "accuracy": float(accuracy_score(all_labels_arr, preds)),
        "auc": float(roc_auc_score(all_labels_arr, all_probs_arr))
        if len(np.unique(all_labels_arr)) > 1
        else 0.0,
    }


def calibration_curve(
    y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10
) -> tuple[np.ndarray, np.ndarray]:
    """Compute calibration curve (fraction of positives vs mean predicted prob).

    Returns:
        ``(fraction_of_positives, mean_predicted_probs)``
    """
    from sklearn.calibration import calibration_curve as _cc
    return _cc(y_true, y_prob, n_bins=n_bins)


def plot_vulnerability_trajectory(
    trajectory: list[float],
    save_path: str | Path | None = None,
    threshold: float = 0.5,
) -> None:
    """Plot *trajectory* as a time series with an optional migraine threshold line.

    Args:
        trajectory: List of vulnerability scores (one per time step).
        save_path:  If provided, save the figure to this path; otherwise display it.
        threshold:  Horizontal dashed line marking the migraine threshold.
    """
    if not _HAS_MPL:
        raise ImportError("matplotlib is required for plotting. Run: pip install -e .[dev] or pip install matplotlib")

    fig, ax = plt.subplots(figsize=(10, 4))
    steps = list(range(len(trajectory)))
    ax.plot(steps, trajectory, marker="o", linewidth=2, label="Vulnerability score")
    ax.axhline(threshold, color="red", linestyle="--", linewidth=1.5, label=f"Threshold ({threshold})")
    ax.fill_between(
        steps, trajectory, threshold,
        where=[v > threshold for v in trajectory],
        alpha=0.2, color="red", label="Migraine risk zone",
    )
    ax.set_xlabel("Time step (days)")
    ax.set_ylabel("Vulnerability score")
    ax.set_title("Migraine Vulnerability Trajectory")
    ax.set_ylim(0.0, 1.0)
    ax.legend()
    plt.tight_layout()

    if save_path is not None:
        fig.savefig(str(save_path), dpi=150)
        plt.close(fig)
    else:
        plt.show()
