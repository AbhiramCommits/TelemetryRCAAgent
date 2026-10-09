"""PyTorch temporal forecaster model."""

import torch
import torch.nn as nn


class TemporalForecaster(nn.Module):
    def __init__(self, input_dim: int, hidden_dim: int = 32, horizon: int = 6) -> None:
        super().__init__()
        self.conv1 = nn.Conv1d(input_dim, hidden_dim, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.conv2 = nn.Conv1d(hidden_dim, hidden_dim, kernel_size=3, padding=1)
        self.fc = nn.Linear(hidden_dim, input_dim * horizon)
        self.input_dim = input_dim
        self.horizon = horizon

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x shape: (batch, seq_len, input_dim) -> (batch, input_dim, seq_len)
        x = x.permute(0, 2, 1)
        x = self.relu(self.conv1(x))
        x = self.relu(self.conv2(x))
        # Take last time step representation
        x = x[:, :, -1]
        out = self.fc(x)
        # Reshape to (batch, horizon, input_dim)
        out = out.view(-1, self.horizon, self.input_dim)
        return out
