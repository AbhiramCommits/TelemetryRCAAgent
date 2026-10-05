"""Data schemas and dataclasses."""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetricPoint:
    entity: str
    metric: str
    ts: int
    value: float


@dataclass
class LogEvent:
    entity: str
    ts: int
    level: str  # INFO, WARN, ERROR, FATAL
    template_id: int
    message: str


@dataclass
class Window:
    entity: str
    ts_start: int
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class Incident:
    id: str
    entity: str
    ts: int
    score: float
    hypothesis: list[dict[str, Any]] = field(default_factory=list)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    latency_ms: float = 0.0
