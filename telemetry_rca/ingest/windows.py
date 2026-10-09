"""Pure-Python windowed aggregator for local mode and testing."""

from typing import Any, Dict, List

import pandas as pd


def aggregate_windows(df_metrics: pd.DataFrame, window_size: int = 60) -> List[Dict[str, Any]]:
    """Aggregate metric points into tumbling windows: mean, max, std, p95."""
    if df_metrics.empty:
        return []

    df = df_metrics.copy()
    df["window_ts"] = (df["ts"] // window_size) * window_size

    grouped = df.groupby(["entity", "metric", "window_ts"])

    agg_df = grouped["value"].agg(
        mean="mean",
        max="max",
        std=lambda x: x.std() if len(x) > 1 else 0.0,
        p95=lambda x: x.quantile(0.95) if len(x) > 0 else 0.0
    ).reset_index()

    # Pivot metric statistics into wide window features per (entity, window_ts)
    windows = []
    for (entity, ts_start), group in agg_df.groupby(["entity", "window_ts"]):
        features = {}
        for _, row in group.iterrows():
            m = row["metric"]
            features[f"{m}_mean"] = float(row["mean"])
            features[f"{m}_max"] = float(row["max"])
            features[f"{m}_std"] = float(row["std"])
            features[f"{m}_p95"] = float(row["p95"])
        windows.append({
            "entity": entity,
            "ts_start": int(ts_start),
            "features": features
        })

    return windows
