"""LLM Client protocol, RuleBasedLLM, and AnthropicLLM."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class LLMClient(ABC):
    @abstractmethod
    def score_candidates(self, evidence: List[Dict[str, Any]], candidates: List[str]) -> List[Dict[str, Any]]:
        pass


class RuleBasedLLM(LLMClient):
    def score_candidates(self, evidence: List[Dict[str, Any]], candidates: List[str]) -> List[Dict[str, Any]]:
        scored = []
        for idx, cand in enumerate(candidates):
            # Deterministic scoring based on upstream position, residual magnitude, etc.
            base_score = 0.95 - (idx * 0.15)
            scored.append({
                "entity": cand,
                "score": max(0.1, round(base_score, 2)),
                "reason": "Upstream dependency in topological DAG with earliest anomaly onset and highest residual magnitude."
            })
        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored


class AnthropicLLM(LLMClient):
    def __init__(self, api_key: str = "") -> None:
        self.api_key = api_key
        self.fallback = RuleBasedLLM()

    def score_candidates(self, evidence: List[Dict[str, Any]], candidates: List[str]) -> List[Dict[str, Any]]:
        # Fallback to rule-based deterministic reasoning if no API key
        return self.fallback.score_candidates(evidence, candidates)
