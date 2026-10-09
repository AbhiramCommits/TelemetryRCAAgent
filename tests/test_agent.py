"""Tests for LangGraph agent and graph execution bounds."""

from telemetry_rca.agent.report import render_incident_report
from telemetry_rca.agent.runner import run_agent_for_anomalies
from telemetry_rca.detect.detector import Anomaly
from telemetry_rca.store.sqlite_store import SQLiteStore


def test_agent_graph_execution():
    store = SQLiteStore("test_agent.db")
    anom = Anomaly(entity="search-service", ts=1710001000, score=4.5, contributing_signals=["cpu_residual(z=4.5)"])
    incidents = run_agent_for_anomalies(store, [anom])

    assert len(incidents) == 1
    inc = incidents[0]
    assert inc.entity == "search-service"
    assert len(inc.hypothesis) > 0
    assert len(inc.evidence) > 0

    report = render_incident_report(inc)
    assert "# Incident Report" in report
    assert "search-service" in report
