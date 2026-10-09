"""Telemetry store interface."""

from abc import ABC, abstractmethod
from typing import Dict, List

from telemetry_rca.schema import Incident, Window


class TelemetryStore(ABC):
    @abstractmethod
    def write_windows(self, windows: List[Window]) -> None:
        pass

    @abstractmethod
    def read_entity_range(self, entity: str, t0: int, t1: int) -> List[Window]:
        pass

    @abstractmethod
    def write_incident(self, incident: Incident) -> None:
        pass

    @abstractmethod
    def read_incidents(self, entity: str, limit: int = 10) -> List[Incident]:
        pass

    @abstractmethod
    def read_neighbors_range(self, entities: List[str], t0: int, t1: int) -> Dict[str, List[Window]]:
        pass
