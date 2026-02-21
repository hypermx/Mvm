from __future__ import annotations

from typing import TYPE_CHECKING

import numpy as np
import torch
import torch.nn as nn
from torch import Tensor

from backend.data_schema.models import DailyLog
from backend.ingestion.ingestion import DataIngestionPipeline
from models.foundation.model import NeuralStateSpaceModel

_ingestion = DataIngestionPipeline()


class PersonalAdapter(nn.Module):
    """Lightweight per-user adaptation layer on top of NeuralStateSpaceModel.

    Adds:
    - A personal (learnable) threshold parameter.
    - A small adapter linear layer that re-scales the base model's latent output.
    """

    def __init__(self, base_model: NeuralStateSpaceModel, user_id: str) -> None:
        super().__init__()
        self.base_model = base_model
        self.user_id = user_id

        latent_dim = base_model.latent_dim
        self.adapter = nn.Linear(latent_dim, latent_dim)
        # Initialise adapter as identity to preserve base-model behaviour.
        nn.init.eye_(self.adapter.weight)
        nn.init.zeros_(self.adapter.bias)

        self.personal_threshold = nn.Parameter(
            base_model.threshold.data.clone()
        )

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        """Forward through base GRU → adapter → vulnerability/prob heads.

        Args:
            x: ``(batch, seq_len, input_dim)``

        Returns:
            vulnerability_trajectory: ``(batch, seq_len, 1)``
            migraine_probs:           ``(batch, seq_len, 1)``
        """
        hidden_seq, _ = self.base_model.gru(x)
        latent = torch.tanh(self.base_model.encoder_proj(hidden_seq))  # (B, T, L)
        adapted_latent = self.adapter(latent)                           # (B, T, L)
        vuln = self.base_model.vulnerability_head(adapted_latent)       # (B, T, 1)
        tau = torch.clamp(self.base_model.temperature, min=1e-3)
        probs = torch.sigmoid((vuln - self.personal_threshold) / tau)
        return vuln, probs

    # ------------------------------------------------------------------
    # Personal fine-tuning
    # ------------------------------------------------------------------

    def fit_personal(self, logs: list[DailyLog], epochs: int = 50, lr: float = 1e-3) -> dict:
        """Fine-tune the adapter and personal threshold on *logs*.

        Only the adapter parameters and personal_threshold are updated;
        the base model weights are frozen.
        """
        if len(logs) < 2:
            return {"loss_history": []}

        # Freeze base model.
        for param in self.base_model.parameters():
            param.requires_grad_(False)

        optimizer = torch.optim.Adam(
            [p for p in self.parameters() if p.requires_grad], lr=lr
        )
        criterion = nn.BCELoss()

        features = np.stack(
            [
                _ingestion.normalize_features(_ingestion.handle_missing_data(lg))
                for lg in logs
            ]
        )
        labels = np.array([1.0 if lg.migraine_occurred else 0.0 for lg in logs], dtype=np.float32)
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0)  # (1, T, F)
        y = torch.tensor(labels, dtype=torch.float32).unsqueeze(0).unsqueeze(-1)  # (1, T, 1)

        loss_history: list[float] = []
        self.train()
        for _ in range(epochs):
            optimizer.zero_grad()
            _, probs = self.forward(x)
            loss = criterion(probs, y)
            loss.backward()
            optimizer.step()
            loss_history.append(float(loss.item()))

        self.eval()
        # Unfreeze base model.
        for param in self.base_model.parameters():
            param.requires_grad_(True)

        return {"loss_history": loss_history}
