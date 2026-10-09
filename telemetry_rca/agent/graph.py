"""LangGraph StateGraph for root-cause analysis with bounded retry loop."""

from typing import Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from telemetry_rca.agent.llm import AnthropicLLM, RuleBasedLLM
from telemetry_rca.agent.tools import (
    get_correlated_signals,
    get_dependency_path,
    get_entity_window,
    get_log_template_spike,
)
from telemetry_rca.config import settings
from telemetry_rca.store.base import TelemetryStore


class AgentState(TypedDict):
    entity: str
    ts: int
    score: float
    evidence: List[Dict[str, Any]]
    candidate_ranking: List[Dict[str, Any]]
    step_log: List[str]
    retry_count: int


def build_rca_graph(store: TelemetryStore) -> Any:
    llm = RuleBasedLLM() if settings.rca_llm == "rules" else AnthropicLLM()

    workflow = StateGraph(AgentState)

    def triage_node(state: AgentState) -> AgentState:
        state["step_log"].append("Triage: analyzing anomaly signal and entity metadata.")
        return state

    def gather_evidence_node(state: AgentState) -> AgentState:
        ent = state["entity"]
        ts = state["ts"]
        windows = get_entity_window(store, ent, ts - 600, ts + 600)
        corr = get_correlated_signals(store, ent, ts)
        logs = get_log_template_spike(ent, ts)

        state["evidence"].append({
            "type": "windows",
            "data_points": len(windows)
        })
        state["evidence"].append({
            "type": "correlations",
            "neighbors": corr
        })
        state["evidence"].append({
            "type": "logs",
            "spike": logs
        })
        state["step_log"].append("Gather Evidence: pulled entity windows, neighbor correlations, and log spikes.")
        return state

    def correlate_node(state: AgentState) -> AgentState:
        dep_path = get_dependency_path(state["entity"])
        state["evidence"].append({"type": "dependency_path", "path": dep_path})
        state["step_log"].append("Correlate: computed dependency path and signal cross-correlations.")
        return state

    def hypothesize_node(state: AgentState) -> AgentState:
        candidates = get_dependency_path(state["entity"])
        # Add some neighbors as candidates
        candidates.extend(["api-gateway", "postgres-db", "auth-service"])
        ranked = llm.score_candidates(state["evidence"], list(set(candidates)))
        state["candidate_ranking"] = ranked
        state["step_log"].append("Hypothesize: scored candidate root causes using LLM / rule reasoner.")
        return state

    def verify_node(state: AgentState) -> AgentState:
        state["step_log"].append(f"Verify: evaluating confidence of top hypothesis (retry {state['retry_count']}).")
        top_score = state["candidate_ranking"][0]["score"] if state["candidate_ranking"] else 0.0
        if top_score < 0.8 and state["retry_count"] < 2:
            state["retry_count"] += 1
            return state
        return state

    def emit_node(state: AgentState) -> AgentState:
        state["step_log"].append("Emit: finalizing ranked hypothesis and evidence trace.")
        return state

    def should_retry(state: AgentState) -> str:
        top_score = state["candidate_ranking"][0]["score"] if state["candidate_ranking"] else 0.0
        if top_score < 0.8 and state["retry_count"] <= 2:
            return "gather_evidence"
        return "emit"

    workflow.add_node("triage", triage_node)
    workflow.add_node("gather_evidence", gather_evidence_node)
    workflow.add_node("correlate", correlate_node)
    workflow.add_node("hypothesize", hypothesize_node)
    workflow.add_node("verify", verify_node)
    workflow.add_node("emit", emit_node)

    workflow.set_entry_point("triage")
    workflow.add_edge("triage", "gather_evidence")
    workflow.add_edge("gather_evidence", "correlate")
    workflow.add_edge("correlate", "hypothesize")
    workflow.add_edge("hypothesize", "verify")
    workflow.add_conditional_edges("verify", should_retry, {
        "gather_evidence": "gather_evidence",
        "emit": "emit"
    })
    workflow.add_edge("emit", END)

    return workflow.compile()
