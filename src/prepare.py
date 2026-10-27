"""Validate and clean source records without fitting imputers."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from src.config import load_config, project_path


def prepare_data(input_path: Path, output_path: Path, config: dict) -> pd.DataFrame:
    """Clean duplicates and implausible demographic rows using configured rules."""
    frame = pd.read_csv(input_path)
    before = len(frame)
    frame = frame.drop_duplicates().copy()
    data = config["data"]
    age = data["age_column"]
    employment = data["employment_length_column"]
    frame = frame[frame[age].between(data["min_age"], data["max_age"], inclusive="both")]
    frame = frame[frame[employment].isna() | (frame[employment] <= frame[age] - data["minimum_working_age"])]
    income = data["income_column"]
    if data["income_cap_enabled"]:
        cap = frame[income].quantile(data["income_cap_quantile"])
        frame[income] = frame[income].clip(upper=cap)
    required = config["project"]["feature_columns"] + [config["project"]["target_column"]]
    frame = frame[required].reset_index(drop=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    print(f"Prepared {len(frame)} rows from {before}; wrote {output_path}")
    return frame


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None)
    parser.add_argument("--output", default=None)
    args = parser.parse_args()
    config = load_config()
    prepare_data(
        project_path(args.input or config["data"]["raw_path"]),
        project_path(args.output or config["data"]["processed_path"]),
        config,
    )


if __name__ == "__main__":
    main()
