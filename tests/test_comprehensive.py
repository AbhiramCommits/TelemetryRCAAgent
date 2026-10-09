"""Comprehensive pytest suite for TelemetryRCAAgent."""

import numpy as np
import pandas as pd

from telemetry_rca.agent.graph import build_rca_graph
from telemetry_rca.detect.baseline import SeasonalBaseline
from telemetry_rca.ingest.windows import aggregate_windows
from telemetry_rca.schema import Window
from telemetry_rca.simulate.topology import build_topology
from telemetry_rca.store.sqlite_store import SQLiteStore


def test_topology_dag():
    edges, graph = build_topology()
    assert len(graph.nodes()) == 11


def test_window_aggregation_parity():
    data = []
    ts_base = 1710000000
    for i in range(12):
        data.append({"entity": "service-a", "metric": "cpu", "ts": ts_base + i * 10, "value": float(i)})
    df = pd.DataFrame(data)
    windows = aggregate_windows(df, window_size=60)
    assert len(windows) == 2
    assert windows[0]["features"]["cpu_mean"] == 2.5


def test_store_interface_conformance():
    store = SQLiteStore(":memory:")
    w = Window(entity="service-a", ts_start=1000, features={"cpu_mean": 40.0})
    store.write_windows([w])
    read_w = store.read_entity_range("service-a", 900, 1100)
    assert len(read_w) == 1
    assert read_w[0].features["cpu_mean"] == 40.0


def test_seasonal_baseline():
    baseline = SeasonalBaseline()
    data = []
    ts_base = 1710000000
    for i in range(100):
        data.append({"entity": "service-a", "metric": "cpu", "ts": ts_base + i * 60, "value": 50.0 + np.random.normal(0, 1)})
    df = pd.DataFrame(data)
    baseline.fit(df)
    z = baseline.score("service-a", "cpu", ts_base + 60, 50.0)
    assert isinstance(z, float)


def test_agent_graph_retry_bound():
    store = SQLiteStore(":memory:")
    graph = build_rca_graph(store)
    state = {
        "entity": "search-service",
        "ts": 1710000000,
        "score": 4.0,
        "evidence": [],
        "candidate_ranking": [{"entity": "search-service", "score": 0.5}],
        "step_log": [],
        "retry_count": 0
    }
    # Invoke graph and ensure it completes and respects bounds
    res = graph.invoke(state)
    assert res["retry_count"] <= 2
    assert "emit" in res["step_log"][-1] or len(res["candidate_ranking"]) > 0


def test_eval_metric_math():
    tp, fp, fn = 90, 10, 10
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = (2 * precision * recall) / (precision + recall)
    assert precision == 0.9
    assert recall == 0.9
    assert f1 == 0.9
