"""CLI script to generate dataset."""

import argparse
import json
from pathlib import Path

from telemetry_rca.simulate.faults import inject_faults
from telemetry_rca.simulate.generator import generate_telemetry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic telemetry dataset"
    )
    parser.add_argument("--days", type=int, default=14, help="Number of days")
    parser.add_argument(
        "--faults", type=int, default=60, help="Number of fault episodes"
    )
    parser.add_argument("--seed", type=int, default=7, help="Random seed")
    args = parser.parse_args()

    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    print(f"Generating telemetry for {args.days} days with seed {args.seed}...")
    df_metrics, df_logs = generate_telemetry(days=args.days, seed=args.seed)

    print(f"Injecting {args.faults} faults...")
    df_metrics, df_logs, labels = inject_faults(
        df_metrics, df_logs, num_faults=args.faults, seed=args.seed
    )

    metrics_path = data_dir / "metrics.parquet"
    logs_path = data_dir / "logs.parquet"
    labels_path = data_dir / "labels.json"

    df_metrics.to_parquet(metrics_path, index=False)
    df_logs.to_parquet(logs_path, index=False)
    with open(labels_path, "w") as f:
        # numpy scalars (e.g. int64 timestamps) are not JSON-serializable as-is
        json.dump(labels, f, indent=2, default=lambda o: o.item())

    print(f"Done! Wrote {len(df_metrics)} metric rows to {metrics_path}")
    print(f"Wrote {len(df_logs)} log rows to {logs_path}")
    print(f"Wrote {len(labels['faults'])} fault labels to {labels_path}")


if __name__ == "__main__":
    main()
