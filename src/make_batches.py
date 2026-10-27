"""Create cumulative, stratified data snapshots for DVC version demonstrations."""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split

from src.config import load_config, project_path


def make_batches(input_path: Path, output_dir: Path, fractions: list[float], seed: int, target: str) -> list[Path]:
    """Write ordered cumulative snapshots from disjoint stratified partitions."""
    if not fractions or abs(sum(fractions) - 1.0) > 1e-8:
        raise ValueError("Configured batch fractions must sum to one.")
    frame = pd.read_csv(input_path)
    partitions: list[pd.DataFrame] = []
    remaining = frame.copy()
    remaining_fraction = 1.0
    for index, fraction in enumerate(fractions):
        if index == len(fractions) - 1:
            partitions.append(remaining)
            break
        relative = fraction / remaining_fraction
        current, remaining = train_test_split(
            remaining, train_size=relative, random_state=seed + index, stratify=remaining[target]
        )
        partitions.append(current)
        remaining_fraction -= fraction
    output_dir.mkdir(parents=True, exist_ok=True)
    cumulative: list[pd.DataFrame] = []
    paths: list[Path] = []
    for index, part in enumerate(partitions, start=1):
        cumulative.append(part)
        destination = output_dir / f"version_{index}.csv"
        pd.concat(cumulative).sample(frac=1, random_state=seed).to_csv(destination, index=False)
        paths.append(destination)
        print(f"Wrote {destination} with {sum(map(len, cumulative))} rows")
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None)
    parser.add_argument("--output-dir", default=None)
    args = parser.parse_args()
    config = load_config()
    make_batches(
        project_path(args.input or config["data"]["raw_path"]),
        project_path(args.output_dir or config["data"]["batches_dir"]),
        config["data"]["batch_fractions"],
        config["data"]["random_seed"],
        config["project"]["target_column"],
    )


if __name__ == "__main__":
    main()
