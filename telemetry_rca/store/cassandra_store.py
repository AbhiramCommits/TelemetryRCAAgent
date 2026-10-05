"""Cassandra store implementing TelemetryStore interface with wide-row reads."""

import json
from typing import List, Dict, Any
from cassandra.cluster import Cluster
from telemetry_rca.store.base import TelemetryStore
from telemetry_rca.schema import Window, Incident


class CassandraStore(TelemetryStore):
    def __init__(self, hosts: list[str] = ["127.0.0.1"], keyspace: str = "telemetry") -> None:
        self.cluster = Cluster(hosts)
        self.session = self.cluster.connect()
        self.keyspace = keyspace
        self._init_schema()

    def _init_schema(self) -> None:
        self.session.execute(f"""
            CREATE KEYSPACE IF NOT EXISTS {self.keyspace}
            WITH replication = {{'class': 'SimpleStrategy', 'replication_factor': 1}}
        """)
        self.session.set_keyspace(self.keyspace)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS windows_by_entity (
                entity text,
                day text,
                ts_start bigint,
                features text,
                PRIMARY KEY ((entity, day), ts_start)
            ) WITH CLUSTERING ORDER BY (ts_start DESC)
        """)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS incidents_by_entity (
                entity text,
                ts bigint,
                id text,
                score float,
                hypothesis text,
                evidence text,
                latency_ms float,
                PRIMARY KEY (entity, ts)
            ) WITH CLUSTERING ORDER BY (ts DESC)
        """)
        self.session.execute("""
            CREATE TABLE IF NOT EXISTS incidents_by_id (
                id text PRIMARY KEY,
                entity text,
                ts bigint,
                score float,
                hypothesis text,
                evidence text,
                latency_ms float
            )
        """)

    def _get_day(self, ts: int) -> str:
        return str(ts // 86400)

    def write_windows(self, windows: List[Window]) -> None:
        query = self.session.prepare("""
            INSERT INTO windows_by_entity (entity, day, ts_start, features)
            VALUES (?, ?, ?, ?)
        """)
        for w in windows:
            day = self._get_day(w.ts_start)
            self.session.execute(query, (w.entity, day, w.ts_start, json.dumps(w.features)))

    def read_entity_range(self, entity: str, t0: int, t1: int) -> List[Window]:
        day0 = self._get_day(t0)
        day1 = self._get_day(t1)
        days = set([day0, day1]) # simplified day span
        
        query = self.session.prepare("""
            SELECT entity, ts_start, features FROM windows_by_entity
            WHERE entity = ? AND day = ? AND ts_start >= ? AND ts_start <= ?
        """)
        
        result = []
        for day in days:
            rows = self.session.execute(query, (entity, day, t0, t1))
            for r in rows:
                result.append(Window(
                    entity=r.entity,
                    ts_start=r.ts_start,
                    features=json.loads(r.features)
                ))
        result.sort(key=lambda x: x.ts_start)
        return result

    def write_incident(self, incident: Incident) -> None:
        day = self._get_day(incident.ts)
        q1 = self.session.prepare("""
            INSERT INTO incidents_by_entity (entity, ts, id, score, hypothesis, evidence, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        q2 = self.session.prepare("""
            INSERT INTO incidents_by_id (id, entity, ts, score, hypothesis, evidence, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """)
        hyp_str = json.dumps(incident.hypothesis)
        ev_str = json.dumps(incident.evidence)
        self.session.execute(q1, (incident.entity, incident.ts, incident.id, incident.score, hyp_str, ev_str, incident.latency_ms))
        self.session.execute(q2, (incident.id, incident.entity, incident.ts, incident.score, hyp_str, ev_str, incident.latency_ms))

    def read_incidents(self, entity: str, limit: int = 10) -> List[Incident]:
        query = self.session.prepare("""
            SELECT id, entity, ts, score, hypothesis, evidence, latency_ms FROM incidents_by_entity
            WHERE entity = ? LIMIT ?
        """)
        rows = self.session.execute(query, (entity, limit))
        result = []
        for r in rows:
            result.append(Incident(
                id=r.id,
                entity=r.entity,
                ts=r.ts,
                score=r.score,
                hypothesis=json.loads(r.hypothesis),
                evidence=json.loads(r.evidence),
                latency_ms=r.latency_ms
            ))
        return result

    def read_neighbors_range(self, entities: List[str], t0: int, t1: int) -> Dict[str, List[Window]]:
        res = {}
        for ent in entities:
            res[ent] = self.read_entity_range(ent, t0, t1)
        return res
