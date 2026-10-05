"""Fault injection module for synthetic telemetry."""

import random

import networkx as nx
import numpy as np
import pandas as pd

from telemetry_rca.simulate.topology import build_topology, get_entities


def inject_faults(
    df_metrics: pd.DataFrame, df_logs: pd.DataFrame, num_faults: int = 60, seed: int = 42
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    random.seed(seed)
    np.random.seed(seed)

    _, graph = build_topology()
    entities = get_entities()
    fault_types = [
        "cpu_saturation",
        "memory_leak",
        "dependency_latency",
        "packet_loss",
        "config_error",
    ]

    min_ts = df_metrics["ts"].min()
    max_ts = df_metrics["ts"].max()
    span = max_ts - min_ts

    fault_records = []
    for i in range(num_faults):
        ftype = random.choice(fault_types)
        root_entity = random.choice(entities)
        fault_start = min_ts + int(random.uniform(0.1, 0.85) * span)
        duration = random.randint(1800, 7200)
        fault_end = fault_start + duration

        fault_id = f"fault_{i}_{ftype}_{root_entity}"
        fault_records.append({
            "id": fault_id,
            "type": ftype,
            "root_entity": root_entity,
            "start_ts": fault_start,
            "end_ts": fault_end,
        })

        downstream = (
            list(nx.descendants(graph, root_entity))
            if hasattr(nx, "descendants")
            else []
        )
        affected_entities = [root_entity] + downstream

        mask_time = (df_metrics["ts"] >= fault_start) & (
            df_metrics["ts"] <= fault_end
        )
        mask_entity = df_metrics["entity"].isin(affected_entities)

        if ftype == "cpu_saturation":
            sub_mask = mask_time & mask_entity & (df_metrics["metric"] == "cpu")
            df_metrics.loc[sub_mask, "value"] = np.clip(
                df_metrics.loc[sub_mask, "value"] * 1.8 + 25.0, 0, 100
            )
        elif ftype == "memory_leak":
            sub_mask = mask_time & mask_entity & (df_metrics["metric"] == "mem")
            df_metrics.loc[sub_mask, "value"] = np.clip(
                df_metrics.loc[sub_mask, "value"] * 1.5 + 30.0, 0, 100
            )
        elif ftype == "dependency_latency":
            sub_mask = (
                mask_time & mask_entity & (df_metrics["metric"] == "latency_p99")
            )
            df_metrics.loc[sub_mask, "value"] = (
                df_metrics.loc[sub_mask, "value"] * 4.5 + 150.0
            )
        elif ftype == "packet_loss":
            sub_mask = (
                mask_time & mask_entity & (df_metrics["metric"] == "error_rate")
            )
            df_metrics.loc[sub_mask, "value"] = np.clip(
                df_metrics.loc[sub_mask, "value"] * 5.0 + 15.0, 0, 100
            )
        elif ftype == "config_error":
            sub_mask = (
                mask_time & mask_entity & (df_metrics["metric"] == "error_rate")
            )
            df_metrics.loc[sub_mask, "value"] = np.clip(
                df_metrics.loc[sub_mask, "value"] * 8.0 + 40.0, 0, 100
            )

        if ftype in ["config_error", "packet_loss"]:
            new_logs = []
            for ent in affected_entities:
                for t_sample in range(fault_start, fault_end, 60):
                    if random.random() < 0.3:
                        new_logs.append({
                            "entity": ent,
                            "ts": t_sample,
                            "level": "ERROR" if ftype == "packet_loss" else "FATAL",
                            "template_id": 4 if ftype == "packet_loss" else 5,
                            "message": f"Injected fault error for {ftype}",
                        })
            if new_logs:
                df_logs = pd.concat([df_logs, pd.DataFrame(new_logs)], ignore_index=True)

    labels = {"faults": fault_records}
    return df_metrics, df_logs, labels
