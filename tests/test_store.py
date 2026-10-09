"""Tests for TelemetryStore interface conformance."""

from pathlib import Path

from telemetry_rca.schema import Incident, Window
from telemetry_rca.store.sqlite_store import SQLiteStore


def test_sqlite_store_conformance():
    db_path = "test_store.db"
    Path(db_path).unlink(missing_ok=True)
    store = SQLiteStore(db_path)

    w1 = Window(entity="service-a", ts_start=1000, features={"cpu_mean": 50.0})
    w2 = Window(entity="service-a", ts_start=1060, features={"cpu_mean": 55.0})
    store.write_windows([w1, w2])

    windows = store.read_entity_range("service-a", 1000, 1100)
    assert len(windows) == 2
    assert windows[0].features["cpu_mean"] == 50.0

    incident = Incident(
        id="inc-1",
        entity="service-a",
        ts=1060,
        score=0.95,
        hypothesis=[{"entity": "service-a", "score": 0.9}],
        evidence=[{"type": "cpu_spike"}],
        latency_ms=12.5
    )
    store.write_incident(incident)

    incidents = store.read_incidents("service-a")
    assert len(incidents) == 1
    assert incidents[0].id == "inc-1"
    assert incidents[0].score == 0.95

    Path(db_path).unlink(missing_ok=True)
