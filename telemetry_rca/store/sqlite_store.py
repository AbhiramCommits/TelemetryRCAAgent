"""SQLite local fallback store implementing TelemetryStore interface."""

import json
import sqlite3
from typing import Dict, List

from telemetry_rca.schema import Incident, Window
from telemetry_rca.store.base import TelemetryStore


class SQLiteStore(TelemetryStore):
    def __init__(self, db_path: str = "telemetry_local.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path)
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
        conn.close()

    def _get_conn(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            # For in-memory sqlite, reuse connection or re-initialize table on same connection if possible
            if not hasattr(self, "_memory_conn"):
                self._memory_conn = sqlite3.connect(":memory:")
                self._memory_conn.row_factory = sqlite3.Row
                self._memory_conn.execute("""
                    CREATE TABLE IF NOT EXISTS windows_by_entity (
                        entity TEXT,
                        ts_start INTEGER,
                        features TEXT,
                        PRIMARY KEY (entity, ts_start)
                    )
                """)
                self._memory_conn.execute("""
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
                self._memory_conn.commit()
            return self._memory_conn

        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def write_windows(self, windows: List[Window]) -> None:
        conn = self._get_conn()
        data = [
            (w.entity, w.ts_start, json.dumps(w.features))
            for w in windows
        ]
        conn.executemany("""
            INSERT OR REPLACE INTO windows_by_entity (entity, ts_start, features)
            VALUES (?, ?, ?)
        """, data)
        conn.commit()
        if self.db_path != ":memory:":
            conn.close()

    def read_entity_range(self, entity: str, t0: int, t1: int) -> List[Window]:
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT entity, ts_start, features FROM windows_by_entity
            WHERE entity = ? AND ts_start >= ? AND ts_start <= ?
            ORDER BY ts_start ASC
        """, (entity, t0, t1))
        rows = cursor.fetchall()
        if self.db_path != ":memory:":
            conn.close()
        result = []
        for r in rows:
            result.append(Window(
                entity=r["entity"],
                ts_start=r["ts_start"],
                features=json.loads(r["features"])
            ))
        return result

    def write_incident(self, incident: Incident) -> None:
        conn = self._get_conn()
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
        if self.db_path != ":memory:":
            conn.close()

    def read_incidents(self, entity: str, limit: int = 10) -> List[Incident]:
        conn = self._get_conn()
        cursor = conn.execute("""
            SELECT id, entity, ts, score, hypothesis, evidence, latency_ms FROM incidents
            WHERE entity = ?
            ORDER BY ts DESC LIMIT ?
        """, (entity, limit))
        rows = cursor.fetchall()
        if self.db_path != ":memory:":
            conn.close()
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
