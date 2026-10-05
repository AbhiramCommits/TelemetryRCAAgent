"""Training script for temporal forecaster model."""

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from pathlib import Path
import pickle

from telemetry_rca.detect.model import TemporalForecaster
from telemetry_rca.detect.baseline import SeasonalBaseline
from telemetry_rca.simulate.topology import get_entities


def train_models(metrics_path: str = "data/metrics.parquet") -> None:
    print("Loading metrics for training...")
    df = pd.read_parquet(metrics_path)
    
    # Train baseline
    print("Fitting seasonal baseline...")
    baseline = SeasonalBaseline()
    baseline.fit(df)

    models_dir = Path("models")
    models_dir.mkdir(parents=True, exist_ok=True)
    with open(models_dir / "baseline.pkl", "wb") as f:
        pickle.dump(baseline, f)

    # Train lightweight PyTorch model on entity groups
    entities = get_entities()
    metrics = ["cpu", "mem", "latency_p99", "error_rate", "throughput"]
    
    # Pivot to wide format per entity: index ts, columns metrics
    print("Training PyTorch temporal forecasters...")
    torch.manual_seed(42)
    np.random.seed(42)

    for entity in entities[:3]:  # train per entity group to keep lightweight & fast
        ent_df = df[df.entity == entity].pivot(index="ts", columns="metric", values="value").dropna()
        if len(ent_df) < 100:
            continue
        
        values = ent_df[metrics].values
        # Normalize
        mean = values.mean(axis=0)
        std = values.std(axis=0) + 1e-5
        norm_vals = (values - mean) / std

        # Create sliding windows of 60 steps -> 6 horizon
        X, Y = [], []
        seq_len = 60
        horizon = 6
        for i in range(len(norm_vals) - seq_len - horizon):
            X.append(norm_vals[i : i + seq_len])
            Y.append(norm_vals[i + seq_len : i + seq_len + horizon])

        if not X:
            continue

        X_t = torch.tensor(np.array(X), dtype=torch.float32)
        Y_t = torch.tensor(np.array(Y), dtype=torch.float32)

        model = TemporalForecaster(input_dim=len(metrics), hidden_dim=16, horizon=horizon)
        optimizer = optim.Adam(model.parameters(), lr=0.01)
        criterion = nn.MSELoss()

        model.train()
        for epoch in range(3):  # quick training epochs
            optimizer.zero_grad()
            preds = model(X_t[:500])  # batch sample
            loss = criterion(preds, Y_t[:500])
            loss.backward()
            optimizer.step()

        torch.save({
            "model_state": model.state_dict(),
            "mean": mean,
            "std": std
        }, models_dir / f"model_{entity}.pt")

    print("Training complete! Models saved to models/")


if __name__ == "__main__":
    train_models()
