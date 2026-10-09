"""Runner to execute LangGraph agent over detected anomalies."""

import time
import uuid
from typing import List

from telemetry_rca.agent.graph import build_rca_graph
from telemetry_rca.detect.detector import Anomaly
from telemetry_rca.schema import Incident
from telemetry_rca.store.base import TelemetryStore


def run_agent_for_anomalies(store: TelemetryStore, anomalies: List[Anomaly]) -> List[Incident]:
    app = build_rca_graph(store)
    incidents = []

    for anom in anomalies[:10]:  # process top anomalies
        t0 = time.time()
        initial_state = {
            "entity": anom.entity,
            "ts": anom.ts,
            "score": anom.score,
            "evidence": [],
            "candidate_ranking": [],
            "step_log": [],
            "retry_count": 0
        }

        final_state = app.invoke(initial_state)
        latency_ms = (time.time() - t0) * 1000

        incident = Incident(
            id=f"inc_{uuid.uuid4().hex[:8]}",
            entity=anom.entity,
            ts=anom.ts,
            score=anom.score,
            hypothesis=final_state.get("candidate_ranking", []),
            evidence=final_state.get("evidence", []),
            latency_ms=latency_ms
        )
        store.write_incident(incident)
        incidents.append(incident)

    return incidents
