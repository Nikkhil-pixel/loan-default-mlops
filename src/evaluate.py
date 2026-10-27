"""Evaluate the selected trained pipeline and emit a DVC-friendly metrics file."""
from __future__ import annotations

import argparse
import json

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient

from src.config import load_config, project_path
from src.metrics import classification_metrics, log_evaluation_artifacts


def evaluate(config: dict) -> dict:
    """Score the best run on the held-out set and store a compact metrics report."""
    mlflow.set_tracking_uri(config["registry"]["tracking_uri"])
    client = MlflowClient(tracking_uri=config["registry"]["tracking_uri"])
    summary = json.loads(project_path(config["paths"]["training_summary_path"]).read_text(encoding="utf-8"))
    test = pd.read_csv(project_path(config["data"]["test_path"]))
    project = config["project"]
    model = mlflow.sklearn.load_model(f"runs:/{summary['best_run_id']}/pipeline")
    positive_index = list(model.classes_).index(project["positive_class"])
    probabilities = model.predict_proba(test[project["feature_columns"]])[:, positive_index]
    binary_y = (test[project["target_column"]].to_numpy() == project["positive_class"]).astype(int)
    raw = classification_metrics(binary_y, probabilities, config["models"]["decision_threshold"])
    result = {key: value for key, value in raw.items() if isinstance(value, float | int)}
    result["confusion_matrix"] = raw["confusion_matrix"]
    result["best_run_id"] = summary["best_run_id"]
    result["best_version"] = summary["best_version"]
    result["data_version"] = summary["data_version"]
    output = project_path(config["paths"]["metrics_path"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    artifact_dir = output.parent / "evaluation"
    log_evaluation_artifacts(raw, artifact_dir)
    for key, value in result.items():
        if isinstance(value, float | int):
            client.log_metric(summary["best_run_id"], key, float(value))
    client.log_artifacts(summary["best_run_id"], str(artifact_dir), artifact_path="final_evaluation")
    print(json.dumps(result, indent=2))
    return result


def main() -> None:
    argparse.ArgumentParser(description=__doc__).parse_args()
    evaluate(load_config())


if __name__ == "__main__":
    main()
