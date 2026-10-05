"""Benchmark script for store performance and range reads."""

import time
import json
from pathlib import Path
import numpy as np
from tabulate import tabulate

from telemetry_rca.store.sqlite_store import SQLiteStore
from telemetry_rca.schema import Window


def run_store_benchmark() -> dict:
    db_path = "telemetry_bench.db"
    Path(db_path).unlink(missing_ok=True)
    store = SQLiteStore(db_path)

    # Ingest 500k window rows across entities
    print("Ingesting 500k window rows into store...")
    entities = [f"entity-{i}" for i in range(10)]
    windows_batch = []
    
    start_ts = 1710000000
    total_rows = 500000
    batch_size = 5000
    
    t0_write = time.time()
    count = 0
    for i in range(total_rows):
        ent = entities[i % len(entities)]
        ts = start_ts + (i // len(entities)) * 60
        windows_batch.append(Window(
            entity=ent,
            ts_start=ts,
            features={"cpu_mean": 45.0, "mem_mean": 60.0, "latency_p99": 15.0}
        ))
        if len(windows_batch) >= batch_size:
            store.write_windows(windows_batch)
            count += len(windows_batch)
            windows_batch = []
    if windows_batch:
        store.write_windows(windows_batch)
        count += len(windows_batch)
    
    write_duration = time.time() - t0_write
    write_throughput = total_rows / write_duration

    print(f"Write throughput: {write_throughput:.2f} rows/sec")

    # Measure p50/p95 latency of 1-hour and 24-hour range reads
    print("Measuring range read latencies...")
    latencies_1h = []
    latencies_24h = []

    for ent in entities:
        # 1-hour read (60 windows)
        t_start = start_ts
        t_end = start_ts + 3600
        t0 = time.time()
        store.read_entity_range(ent, t_start, t_end)
        latencies_1h.append((time.time() - t0) * 1000)

        # 24-hour read (1440 windows)
        t_end_24 = start_ts + 86400
        t0 = time.time()
        store.read_entity_range(ent, t_start, t_end_24)
        latencies_24h.append((time.time() - t0) * 1000)

    p50_1h = float(np.percentile(latencies_1h, 50))
    p95_1h = float(np.percentile(latencies_1h, 95))
    p50_24h = float(np.percentile(latencies_24h, 50))
    p95_24h = float(np.percentile(latencies_24h, 95))

    results = {
        "write_throughput_rows_sec": float(write_throughput),
        "read_1h_p50_ms": p50_1h,
        "read_1h_p95_ms": p95_1h,
        "read_24h_p50_ms": p50_24h,
        "read_24h_p95_ms": p95_24h,
    }

    results_dir = Path("results")
    results_dir.mkdir(parents=True, exist_ok=True)
    with open(results_dir / "store_bench.json", "w") as f:
        json.dump(results, f, indent=2)

    table = [
        ["Metric", "Value"],
        ["Write Throughput", f"{write_throughput:.2f} rows/sec"],
        ["1-Hour Read p50", f"{p50_1h:.2f} ms"],
        ["1-Hour Read p95", f"{p95_1h:.2f} ms"],
        ["24-Hour Read p50", f"{p50_24h:.2f} ms"],
        ["24-Hour Read p95", f"{p95_24h:.2f} ms"],
    ]
    print(tabulate(table, headers="firstrow", tablefmt="grid"))
    Path(db_path).unlink(missing_ok=True)
    return results


if __name__ == "__main__":
    run_store_benchmark()
