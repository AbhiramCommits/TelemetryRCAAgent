"""Producer script to replay dataset to message bus."""

import pandas as pd

from telemetry_rca.config import settings
from telemetry_rca.ingest.bus import KafkaBus, LocalBus, MessageBus


def get_bus() -> MessageBus:
    if settings.backend == "cluster":
        return KafkaBus(settings.kafka_bootstrap_servers)
    return LocalBus()


def replay_dataset(metrics_path: str = "data/metrics.parquet", logs_path: str = "data/logs.parquet", speedup: float = 1000.0) -> int:
    df_metrics = pd.read_parquet(metrics_path)
    bus = get_bus()

    count = 0
    # Replay metrics
    for _, row in df_metrics.iterrows():
        val = {
            "entity": row["entity"],
            "metric": row["metric"],
            "ts": int(row["ts"]),
            "value": float(row["value"])
        }
        bus.produce("telemetry.metrics", row["entity"], val)
        count += 1
        if count % 10000 == 0:
            pass

    return count
