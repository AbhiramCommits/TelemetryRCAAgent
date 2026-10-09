"""CLI script to run end-to-end evaluation."""

import argparse

from telemetry_rca.eval.harness import run_evaluation


def main() -> None:
    parser = argparse.ArgumentParser(description="Run TelemetryRCAAgent evaluation")
    parser.add_argument("--backend", type=str, default="local", choices=["local", "cluster"], help="Backend type")
    args = parser.parse_args()

    run_evaluation(args.backend)


if __name__ == "__main__":
    main()
