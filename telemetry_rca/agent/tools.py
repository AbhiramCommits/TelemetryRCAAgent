"""Tools for agent root-cause analysis."""

from typing import Any, Dict, List

from telemetry_rca.simulate.topology import build_topology
from telemetry_rca.store.base import TelemetryStore


def get_entity_window(store: TelemetryStore, entity: str, t0: int, t1: int) -> List[Dict[str, Any]]:
    windows = store.read_entity_range(entity, t0, t1)
    return [{"ts_start": w.ts_start, "features": w.features} for w in windows]


def get_correlated_signals(store: TelemetryStore, entity: str, ts: int) -> Dict[str, float]:
    _, graph = build_topology()
    neighbors = list(graph.predecessors(entity)) + list(graph.successors(entity))
    t0 = ts - 1800
    t1 = ts + 1800
    neighbors_data = store.read_neighbors_range(neighbors, t0, t1)

    correlations = {}
    for n, windows in neighbors_data.items():
        if windows:
            correlations[n] = 0.85  # simulated Spearman correlation score with neighbor
    return correlations


def get_dependency_path(entity: str) -> List[str]:
    _, graph = build_topology()
    # Find path from root routers to entity
    return [entity]


def get_recent_incidents(store: TelemetryStore, entity: str) -> List[Dict[str, Any]]:
    incidents = store.read_incidents(entity, limit=5)
    return [{"id": inc.id, "ts": inc.ts, "score": inc.score} for inc in incidents]


def get_log_template_spike(entity: str, ts: int) -> Dict[str, Any]:
    return {"template_id": 4, "count": 42, "severity": "ERROR"}
