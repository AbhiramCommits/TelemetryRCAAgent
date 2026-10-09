"""Test suite for parity between pure Python windows and aggregation."""

import pandas as pd

from telemetry_rca.ingest.spark_stream import run_spark_aggregation
from telemetry_rca.ingest.windows import aggregate_windows


def test_window_aggregation_parity():
    # Create sample metrics data
    data = []
    ts_base = 1710000000
    for i in range(12): # 2 minutes of data at 10s intervals
        data.append({"entity": "service-a", "metric": "cpu", "ts": ts_base + i * 10, "value": float(i)})
        data.append({"entity": "service-a", "metric": "mem", "ts": ts_base + i * 10, "value": float(50 + i % 10)})
    df = pd.DataFrame(data)

    windows_py = aggregate_windows(df, window_size=60)
    assert len(windows_py) == 2
    assert windows_py[0]["entity"] == "service-a"
    assert "cpu_mean" in windows_py[0]["features"]


def test_streaming_execution():
    count, throughput = run_spark_aggregation()
    assert count > 0
    assert throughput > 0
    print(f"Produced {count} windows at {throughput:.2f} windows/sec")
