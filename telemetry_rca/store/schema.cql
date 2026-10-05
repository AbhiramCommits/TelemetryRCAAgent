-- CQL Schema for Cassandra Store

CREATE KEYSPACE IF NOT EXISTS telemetry
WITH replication = {'class': 'SimpleStrategy', 'replication_factor': 1};

USE telemetry;

CREATE TABLE IF NOT EXISTS metrics_by_entity (
    entity text,
    day text,
    ts bigint,
    metric text,
    value double,
    PRIMARY KEY ((entity, day), ts, metric)
) WITH CLUSTERING ORDER BY (ts DESC, metric ASC);

CREATE TABLE IF NOT EXISTS windows_by_entity (
    entity text,
    day text,
    ts_start bigint,
    features text,
    PRIMARY KEY ((entity, day), ts_start)
) WITH CLUSTERING ORDER BY (ts_start DESC);

CREATE TABLE IF NOT EXISTS incidents_by_entity (
    entity text,
    ts bigint,
    id text,
    score float,
    hypothesis text,
    evidence text,
    latency_ms float,
    PRIMARY KEY (entity, ts)
) WITH CLUSTERING ORDER BY (ts DESC);

CREATE TABLE IF NOT EXISTS incidents_by_id (
    id text PRIMARY KEY,
    entity text,
    ts bigint,
    score float,
    hypothesis text,
    evidence text,
    latency_ms float
);
