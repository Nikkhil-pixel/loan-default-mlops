"""Create Evidently drift reports from reference data and serving logs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

from src.config import load_config, project_path


def _evidently_result(value: Any, result: dict[str, Any]) -> None:
    """Recursively collect known Evidently result values across compatible report shapes."""
    if isinstance(value, dict):
        for key in ("dataset_drift", "number_of_drifted_columns", "share_of_drifted_columns", "drift_by_columns"):
            if key in value:
                result[key] = value[key]
        for child in value.values():
            _evidently_result(child, result)
    elif isinstance(value, list):
        for child in value:
            _evidently_result(child, result)


def _read_current(path: Path, features: list[str], limit: int) -> pd.DataFrame:
    """Parse JSONL request records and return configured feature columns only."""
    records: list[dict] = []
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    record = json.loads(line)
                    payload = record.get("input", record)
                    if all(feature in payload for feature in features):
                        records.append({feature: payload[feature] for feature in features})
                except (json.JSONDecodeError, TypeError):
                    continue
    return pd.DataFrame(records[-limit:])


def monitor(config: dict[str, Any]) -> dict[str, Any]:
    """Compare serving inputs with training inputs and return drift summary."""
    from evidently.metric_preset import DataDriftPreset
    from evidently.report import Report

    features = config["project"]["feature_columns"]
    reference = pd.read_csv(project_path(config["monitoring"]["reference_path"]))[features]
    current = _read_current(project_path(config["monitoring"]["current_log_path"]), features, config["monitoring"]["sample_limit"])
    output_path = project_path(config["monitoring"]["report_path"])
    summary_path = project_path(config["monitoring"]["summary_path"])
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    if len(current) < config["monitoring"]["minimum_rows"]:
        message = f"Insufficient requests for drift evaluation: {len(current)} observed; {config['monitoring']['minimum_rows']} required."
        output_path.write_text(f"<html><body><h1>Drift report</h1><p>{message}</p></body></html>", encoding="utf-8")
        summary = {"drift_detected": False, "share_of_drifted_columns": 0.0, "drifted_columns": [], "request_rows": len(current), "status": "insufficient_data"}
    else:
        report = Report(metrics=[DataDriftPreset()])
        report.run(reference_data=reference, current_data=current)
        report.save_html(str(output_path))
        raw = report.as_dict()
        extracted: dict[str, Any] = {}
        _evidently_result(raw, extracted)
        drift_map = extracted.get("drift_by_columns", {}) or {}
        drifted = [name for name, item in drift_map.items() if isinstance(item, dict) and item.get("drift_detected")]
        count = len(features)
        share = float(extracted.get("share_of_drifted_columns", len(drifted) / count if count else 0.0))
        detected = share >= config["monitoring"]["drift_share_threshold"]
        summary = {"drift_detected": detected, "share_of_drifted_columns": share, "drifted_columns": drifted, "request_rows": len(current), "status": "complete"}
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    monitor(load_config())


if __name__ == "__main__":
    main()
