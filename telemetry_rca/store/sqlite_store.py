"""SQLite local fallback store implementing TelemetryStore interface."""

import sqlite3
import json
from typing import List, Dict, Any
from telemetry_rca.store.base import TelemetryStore
from telemetry_rca.schema import Window, Incident


class SQLiteStore(TelemetryStore):
    def __init__(self, db_path: str = "telemetry_local.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS windows_by_entity (
                    entity TEXT,
                    ts_start INTEGER,
                    features TEXT,
                    PRIMARY KEY (entity, ts_start)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS incidents (
                    id TEXT PRIMARY KEY,
                    entity TEXT,
                    ts INTEGER,
                    score REAL,
                    hypothesis TEXT,
                    evidence TEXT,
                    latency_ms REAL
                )
            """)
            conn.commit()

    def write_windows(self, windows: List[Window]) -> None:
        with self._get_conn() as conn:
            data = [
                (w.entity, w.ts_start, json.dumps(w.features))
                for w in windows
            ]
            conn.executemany("""
                INSERT OR REPLACE INTO windows_by_entity (entity, ts_start, features)
                VALUES (?, ?, ?)
            """, data)
            conn.commit()

    def read_entity_range(self, entity: str, t0: int, t1: int) -> List[Window]:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT entity, ts_start, features FROM windows_by_entity
                WHERE entity = ? AND ts_start >= ? AND ts_start <= ?
                ORDER BY ts_start ASC
            """, (entity, t0, t1))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append(Window(
                    entity=r["entity"],
                    ts_start=r["ts_start"],
                    features=json.loads(r["features"])
                ))
            return result

    def write_incident(self, incident: Incident) -> None:
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO incidents (id, entity, ts, score, hypothesis, evidence, latency_ms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                incident.id,
                incident.entity,
                incident.ts,
                incident.score,
                json.dumps(incident.hypothesis),
                json.dumps(incident.evidence),
                incident.latency_ms
            ))
            conn.commit()

    def read_incidents(self, entity: str, limit: int = 10) -> List[Incident]:
        with self._get_conn() as conn:
            cursor = conn.execute("""
                SELECT id, entity, ts, score, hypothesis, evidence, latency_ms FROM incidents
                WHERE entity = ?
                ORDER BY ts DESC LIMIT ?
            """, (entity, limit))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                result.append(Incident(
                    id=r["id"],
                    entity=r["entity"],
                    ts=r["ts"],
                    score=r["score"],
                    hypothesis=json.loads(r["hypothesis"]),
                    evidence=json.loads(r["evidence"]),
                    latency_ms=r["latency_ms"]
                ))
            return result

    def read_neighbors_range(self, entities: List[str], t0: int, t1: int) -> Dict[str, List[Window]]:
        res = {}
        for ent in entities:
            res[ent] = self.read_entity_range(ent, t0, t1)
        return res
