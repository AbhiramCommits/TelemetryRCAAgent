"""Anomaly detector combining forecast residual z-score with seasonal baseline."""

import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import torch

from telemetry_rca.detect.baseline import SeasonalBaseline
from telemetry_rca.detect.model import TemporalForecaster
from telemetry_rca.schema import Window
from telemetry_rca.simulate.topology import get_entities


class Anomaly:
    def __init__(self, entity: str, ts: int, score: float, contributing_signals: list[str]) -> None:
        self.entity = entity
        self.ts = ts
        self.score = score
        self.contributing_signals = contributing_signals


class AnomalyDetector:
    def __init__(self, mode: str = "combined") -> None:
        self.mode = mode
        self.baseline = None
        self.models = {}
        self.scalers = {}
        self._load_artifacts()

    def _load_artifacts(self) -> None:
        models_dir = Path("models")
        baseline_path = models_dir / "baseline.pkl"
        if baseline_path.exists():
            with open(baseline_path, "rb") as f:
                self.baseline = pickle.load(f)

        for entity in get_entities():
            m_path = models_dir / f"model_{entity}.pt"
            if m_path.exists():
                checkpoint = torch.load(m_path, map_location="cpu", weights_only=False)
                model = TemporalForecaster(input_dim=5, hidden_dim=16, horizon=6)
                model.load_state_dict(checkpoint["model_state"])
                model.eval()
                self.models[entity] = model
                self.scalers[entity] = (checkpoint["mean"], checkpoint["std"])

    def detect(self, df_metrics: pd.DataFrame, threshold: float = 3.0) -> list[Anomaly]:
        anomalies = []
        metrics = ["cpu", "mem", "latency_p99", "error_rate", "throughput"]

        # Group by entity and check window points
        for entity, group in df_metrics.groupby("entity"):
            group = group.sort_values("ts")
            pivoted = group.pivot(index="ts", columns="metric", values="value").dropna()
            if pivoted.empty:
                continue

            timestamps = pivoted.index.values
            values = pivoted[metrics].values

            for idx in range(60, len(timestamps)):
                ts = int(timestamps[idx])
                contrib = []
                max_score = 0.0

                # 1. Baseline check
                if self.mode in ["combined", "baseline_only"]:
                    for m_idx, m_name in enumerate(metrics):
                        val = values[idx, m_idx]
                        if self.baseline:
                            z = self.baseline.score(entity, m_name, ts, val)
                            if abs(z) > threshold:
                                contrib.append(f"{m_name}_baseline(z={z:.1f})")
                                max_score = max(max_score, abs(z))

                # 2. Model residual check
                if self.mode in ["combined", "model_only"] and entity in self.models:
                    mean, std = self.scalers[entity]
                    norm_seq = (values[idx - 60 : idx] - mean) / std
                    x_t = torch.tensor(norm_seq[np.newaxis, :, :], dtype=torch.float32)
                    with torch.no_grad():
                        pred = self.models[entity](x_t).numpy()[0, 0]  # first horizon step
                    actual_norm = (values[idx] - mean) / std
                    residuals = np.abs(actual_norm - pred)
                    for m_idx, m_name in enumerate(metrics):
                        res_z = residuals[m_idx]
                        if res_z > threshold:
                            contrib.append(f"{m_name}_residual(z={res_z:.1f})")
                            max_score = max(max_score, res_z)

                if contrib:
                    anomalies.append(Anomaly(entity=entity, ts=ts, score=float(max_score), contributing_signals=contrib))

        return anomalies
