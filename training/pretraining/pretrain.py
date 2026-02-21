from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor
from torch.utils.data import DataLoader

from models.foundation.model import NeuralStateSpaceModel


def pretrain(
    model: NeuralStateSpaceModel,
    dataloader: DataLoader,
    epochs: int = 20,
    lr: float = 1e-3,
) -> dict[str, list[float]]:
    """Pre-train *model* on pooled data from *dataloader*.

    Each batch should yield ``(x, y)`` where:
    - ``x``: Tensor ``(batch, seq_len, input_dim)``
    - ``y``: Tensor ``(batch, seq_len, 1)`` – binary migraine labels

    Returns:
        Dict with ``loss_history`` list.
    """
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.BCELoss()
    loss_history: list[float] = []

    model.train()
    for epoch in range(epochs):
        epoch_loss = 0.0
        n_batches = 0
        for x, y in dataloader:
            x = x.float()
            y = y.float()
            optimizer.zero_grad()
            _, probs = model(x)
            loss = criterion(probs, y)
            loss.backward()
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            optimizer.step()
            epoch_loss += float(loss.item())
            n_batches += 1
        avg = epoch_loss / max(n_batches, 1)
        loss_history.append(avg)

    model.eval()
    return {"loss_history": loss_history}
