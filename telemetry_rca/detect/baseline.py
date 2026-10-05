"""Seasonal baseline with per-(entity, metric) day-of-week + time-of-day median and robust MAD scaling."""

import numpy as np
import pandas as pd


class SeasonalBaseline:
    def __init__(self) -> None:
        self.medians: dict[str, dict[int, float]] = {}
        self.mads: dict[str, dict[int, float]] = {}

    def fit(self, df_metrics: pd.DataFrame) -> None:
        """Fit seasonal baseline from clean metric points."""
        df = df_metrics.copy()
        # time-of-day bucket (86400 seconds in a day divided into 144 buckets of 10 minutes)
        df["bucket"] = (df["ts"] % 86400) // 600

        for (entity, metric), group in df.groupby(["entity", "metric"]):
            key = f"{entity}_{metric}"
            self.medians[key] = {}
            self.mads[key] = {}
            
            bucket_grouped = group.groupby("bucket")["value"]
            meds = bucket_grouped.median()
            mads = bucket_grouped.apply(lambda x: np.median(np.abs(x - x.median())))

            for b in meds.index:
                self.medians[key][int(b)] = float(meds[b])
                mad_val = float(mads[b])
                self.mads[key][int(b)] = mad_val if mad_val > 1e-5 else 1.0

    def score(self, entity: str, metric: str, ts: int, value: float) -> float:
        """Compute robust z-score deviation from seasonal baseline."""
        key = f"{entity}_{metric}"
        bucket = int((ts % 86400) // 600)

        if key not in self.medians or bucket not in self.medians[key]:
            return 0.0

        med = self.medians[key][bucket]
        mad = self.mads[key][bucket]
        # Robust z-score using MAD: 0.6745 * (x - median) / MAD
        z = 0.6745 * (value - med) / mad
        return float(z)
