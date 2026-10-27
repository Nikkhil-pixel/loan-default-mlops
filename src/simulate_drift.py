"""Append clean or deliberately shifted reference examples to monitoring JSONL."""
from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime

import pandas as pd

from src.config import load_config, project_path


def simulate(config: dict, clean: bool = False) -> int:
    """Write reproducible reference-like or shifted request examples."""
    settings = config["monitoring"]
    features = config["project"]["feature_columns"]
    frame = pd.read_csv(project_path(settings["reference_path"]))[features]
    rows = frame.sample(n=min(settings["sample_limit"], len(frame)), random_state=config["data"]["random_seed"]).copy()
    if not clean:
        income = config["data"]["income_column"]
        interest = config["data"]["interest_rate_column"]
        ranges = config["project"]["value_ranges"]
        rows[income] = (rows[income] * settings["income_shift_multiplier"]).clip(upper=ranges[income][1])
        rows[interest] = (rows[interest] + settings["interest_rate_shift"]).clip(upper=ranges[interest][1])
    log_path = project_path(settings["current_log_path"])
    log_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).isoformat()
    with log_path.open("a", encoding="utf-8") as handle:
        for row in rows.to_dict(orient="records"):
            record = {"timestamp": timestamp, "model_version": "simulation", "input": row}
            handle.write(json.dumps(record) + "\n")
    label = "clean reference-like" if clean else "shifted"
    print(f"Appended {len(rows)} {label} requests to {log_path}")
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--clean", action="store_true", help="Write unshifted reference examples.")
    args = parser.parse_args()
    simulate(load_config(), clean=args.clean)


if __name__ == "__main__":
    main()
