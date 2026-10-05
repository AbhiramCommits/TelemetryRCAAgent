"""Synthetic telemetry generator with daily seasonality and noise."""

import random

import numpy as np
import pandas as pd

from telemetry_rca.simulate.topology import get_entities


def generate_telemetry(
    days: int = 14, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame]:
    random.seed(seed)
    np.random.seed(seed)

    entities = get_entities()
    start_ts = 1710000000  # arbitrary epoch
    step = 10  # 10 seconds cadence
    total_steps = (days * 24 * 3600) // step

    metric_rows = []
    log_rows = []

    log_templates = [
        (1, "INFO", "Server started successfully"),
        (2, "INFO", "Connection established with client"),
        (3, "WARN", "High memory usage detected"),
        (4, "ERROR", "Database connection timeout"),
        (5, "FATAL", "Uncaught exception in worker thread"),
        (6, "INFO", "Processed request in 12ms"),
    ]

    timestamps = [start_ts + i * step for i in range(total_steps)]

    for entity in entities:
        t_arr = np.array(timestamps)
        daily_phase = (t_arr % 86400) / 86400.0 * 2 * np.pi

        base_cpu = 30.0 + 15.0 * np.sin(daily_phase)
        base_mem = 40.0 + 10.0 * np.cos(daily_phase)
        base_lat = 20.0 + 5.0 * np.sin(daily_phase)
        base_err = 0.1 + 0.05 * np.abs(np.cos(daily_phase))
        base_thru = 1000.0 + 500.0 * np.sin(daily_phase)

        for idx, ts in enumerate(timestamps):
            c = max(1.0, min(100.0, base_cpu[idx] + np.random.normal(0, 3.0)))
            m = max(1.0, min(100.0, base_mem[idx] + np.random.normal(0, 2.0)))
            lat = max(1.0, base_lat[idx] + np.random.exponential(2.0))
            e = max(0.0, min(100.0, base_err[idx] + np.random.exponential(0.05)))
            th = max(10.0, base_thru[idx] + np.random.normal(0, 50.0))

            metric_rows.append({"entity": entity, "metric": "cpu", "ts": ts, "value": c})
            metric_rows.append({"entity": entity, "metric": "mem", "ts": ts, "value": m})
            metric_rows.append(
                {"entity": entity, "metric": "latency_p99", "ts": ts, "value": lat}
            )
            metric_rows.append(
                {"entity": entity, "metric": "error_rate", "ts": ts, "value": e}
            )
            metric_rows.append(
                {"entity": entity, "metric": "throughput", "ts": ts, "value": th}
            )

            if idx % 6 == 0 and random.random() < 0.5:
                tpl = random.choice(log_templates)
                log_rows.append({
                    "entity": entity,
                    "ts": ts,
                    "level": tpl[1],
                    "template_id": tpl[0],
                    "message": tpl[2],
                })

    df_metrics = pd.DataFrame(metric_rows)
    df_logs = pd.DataFrame(log_rows)
    return df_metrics, df_logs
