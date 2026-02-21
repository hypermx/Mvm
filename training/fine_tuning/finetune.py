from __future__ import annotations

import numpy as np
import torch
import torch.nn as nn

from backend.data_schema.models import DailyLog
from models.personal.adapter import PersonalAdapter


def finetune(
    adapter: PersonalAdapter,
    user_logs: list[DailyLog],
    epochs: int = 50,
    lr: float = 1e-3,
) -> dict[str, list[float]]:
    """Fine-tune *adapter* on a single user's *user_logs*.

    Only the adapter parameters and personal_threshold are updated;
    the base model is frozen.

    Returns:
        Dict with ``loss_history`` list.
    """
    result = adapter.fit_personal(user_logs, epochs=epochs, lr=lr)
    return result
