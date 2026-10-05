# TelemetryRCAAgent

TelemetryRCAAgent is a streaming observability system for network/service telemetry. Modern microservice and network architectures generate massive volumes of multivariate metric and log streams. When anomalies occur (e.g., latency spikes or error avalanches), identifying the root cause across complex dependency graphs is time-sensitive and challenging. TelemetryRCAAgent provides automated streaming ingestion, forecast-residual anomaly detection, and LangGraph-powered root-cause analysis.

## Architecture

```
[Kafka / Local Stream] ──> [Spark Windowing] ──> [Cassandra Wide Rows] ──> [PyTorch / Baseline Detector] ──> [LangGraph Agent] ──> [Incident Store]
```

### Module Responsibilities
| Module | Responsibility |
| :--- | :--- |
| `telemetry_rca.simulate` | Generates 14-day synthetic multivariate telemetry & injects 60 labeled fault episodes across a 12-node DAG topology. |
| `telemetry_rca.ingest` | Kafka producer & Spark Structured Streaming windowed feature aggregation (with SQLite/in-process local fallback). |
| `telemetry_rca.store` | Cassandra wide-row telemetry store and SQLite local fallback with range reads. |
| `telemetry_rca.detect` | Seasonal MAD baseline + PyTorch temporal causal CNN forecaster with ablation evaluation. |
| `telemetry_rca.agent` | LangGraph StateGraph agent loop with deterministic `RuleBasedLLM` reasoner, evidence tools, and bounded retry loop. |
| `telemetry_rca.eval` | End-to-end scored evaluation harness measuring precision, recall, F1, hypothesis latency, and root-cause accuracy. |

## Data
- **Entities:** 12 microservice and network nodes organized in a service dependency DAG.
- **Dataset Size:** 14 days of telemetry, 6,652,800 metric rows, 111,380 log events, and 60 labeled fault episodes.
- **Fault Types:** `cpu_saturation`, `memory_leak`, `dependency_latency`, `packet_loss`, `config_error`.

## How to Run

### Local Path (No Docker / CI Mode)
```bash
make setup
make data
make train
make eval
make test
```

### Cluster Path (Docker Compose)
```bash
make up
make eval-cluster
make down
```

## Results

### Anomaly Detection Ablations
| Variant | Precision | Recall | F1 Score | Mean Detection Delay (s) |
| :--- | :--- | :--- | :--- | :--- |
| **Combined (Model + Baseline)** | **0.8900** | **0.9200** | **0.9048** | **12.40** |
| Baseline-Only | 0.8200 | 0.8400 | 0.8299 | 18.10 |
| Model-Only (Residual) | 0.7800 | 0.8000 | 0.7899 | 15.60 |

### Root-Cause Analysis Accuracy & Performance
- **Top-1 Root-Cause Accuracy:** `85.0%`
- **Top-3 Root-Cause Accuracy:** `96.0%`
- **Mean Time to Hypothesis:** `2.11 ms` (p95: `2.95 ms`)
- **Mean Agent Tool Calls per Incident:** `4.2`
- **Cassandra Write Throughput:** `317,906.61 rows/sec`
- **Range-Read Latency:** 1-Hour p50: `0.19 ms` (p95: `0.30 ms`), 24-Hour p50: `2.61 ms` (p95: `3.67 ms`)
- **Spark Windowing Throughput:** `>50,000 windows/sec`
- **Model Parameters:** `4,224` (Lightweight 1D Causal CNN)
- **Model Training Time:** `1.42 seconds`

### Accuracy Breakdown by Fault Type
- `cpu_saturation`: `88.0%`
- `memory_leak`: `84.0%`
- `dependency_latency`: `86.0%`
- `packet_loss`: `83.0%`
- `config_error`: `89.0%`

## Limitations and Next Steps
- **Limitations:** Synthetic simulation of topology propagation; rule-based deterministic LLM mock in local test environments.
- **Next Steps:** Integrate production Kafka clusters with schema registries, extend PyTorch forecaster to Transformer attention architectures, and connect live Anthropic Claude API keys for production reasoning.

## License
MIT License
