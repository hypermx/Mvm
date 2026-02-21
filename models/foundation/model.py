from __future__ import annotations

import torch
import torch.nn as nn
from torch import Tensor


class NeuralStateSpaceModel(nn.Module):
    """GRU-based neural state-space model for migraine vulnerability.

    Latent dynamics:
        h_t = GRU(x_t, h_{t-1})
        v_t = Linear(h_t)          -- latent vulnerability in [0, 1]
        p_t = sigmoid((v_t - θ) / τ)  -- migraine probability

    Args:
        input_dim:  Number of input features per time step.
        hidden_dim: GRU hidden size.
        latent_dim: Dimensionality of the latent vulnerability state.
    """

    def __init__(self, input_dim: int, hidden_dim: int, latent_dim: int) -> None:
        super().__init__()
        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.latent_dim = latent_dim

        self.gru = nn.GRU(input_size=input_dim, hidden_size=hidden_dim, batch_first=True)
        self.encoder_proj = nn.Linear(hidden_dim, latent_dim)
        self.vulnerability_head = nn.Sequential(
            nn.Linear(latent_dim, 1),
            nn.Sigmoid(),
        )
        # Learnable threshold and temperature for the sigmoid crossing.
        self.threshold = nn.Parameter(torch.tensor(0.5))
        self.temperature = nn.Parameter(torch.tensor(0.1))

    # ------------------------------------------------------------------
    # Forward pass
    # ------------------------------------------------------------------

    def forward(self, x: Tensor) -> tuple[Tensor, Tensor]:
        """Run the model on an input sequence.

        Args:
            x: Input tensor of shape ``(batch, seq_len, input_dim)``.

        Returns:
            vulnerability_trajectory: shape ``(batch, seq_len, 1)`` – scores in [0, 1].
            migraine_probs:           shape ``(batch, seq_len, 1)`` – crossing probabilities.
        """
        hidden_seq, _ = self.gru(x)                        # (B, T, H)
        latent = torch.tanh(self.encoder_proj(hidden_seq))  # (B, T, L)
        vuln = self.vulnerability_head(latent)              # (B, T, 1)
        tau = torch.clamp(self.temperature, min=1e-3)
        probs = torch.sigmoid((vuln - self.threshold) / tau)
        return vuln, probs

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------

    def encode_state(self, x: Tensor) -> Tensor:
        """Return the latent vulnerability state for the last time step.

        Args:
            x: Input tensor ``(batch, seq_len, input_dim)``.

        Returns:
            Latent tensor of shape ``(batch, latent_dim)``.
        """
        hidden_seq, _ = self.gru(x)
        latent = torch.tanh(self.encoder_proj(hidden_seq))
        return latent[:, -1, :]   # last step
