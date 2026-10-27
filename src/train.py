"""Train configured classifier pipelines, log experiments, and register candidates."""
from __future__ import annotations

import argparse
import importlib
import json
import subprocess
from pathlib import Path
from typing import Any

import mlflow
import mlflow.sklearn
import pandas as pd
from mlflow import MlflowClient
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.config import load_config, project_path
from src.metrics import classification_metrics, log_evaluation_artifacts


def _resolve_class(path: str) -> type:
    module_name, class_name = path.rsplit(".", 1)
    return getattr(importlib.import_module(module_name), class_name)


def build_pipeline(config: dict[str, Any], model_key: str, positive_weight: float) -> Pipeline:
    """Build one imputation/encoding/scaling/model pipeline from parameters."""
    project = config["project"]
    data = config["data"]
    numeric = project["numeric_features"]
    categorical = project["categorical_features"]
    numeric_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="median", add_indicator=data["missing_indicator"])),
        ("scaler", StandardScaler()),
    ]
    categorical_steps: list[tuple[str, Any]] = [
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore")),
    ]
    transformations = ColumnTransformer(
        [("numeric", Pipeline(numeric_steps), numeric),
         ("categorical", Pipeline(categorical_steps), categorical)]
    )
    model_config = config["models"][model_key]
    parameters = dict(model_config["parameters"])
    imbalance_parameter = model_config.get("imbalance_parameter")
    if imbalance_parameter == "scale_pos_weight":
        parameters[imbalance_parameter] = positive_weight
    elif imbalance_parameter == "class_weight":
        parameters[imbalance_parameter] = "balanced"
    estimator = _resolve_class(model_config["class_path"])(**parameters)
    return Pipeline([("preprocess", transformations), ("classifier", estimator)])


def _data_version(config: dict[str, Any]) -> str:
    raw_path = project_path(config["data"]["raw_path"])
    pointer = raw_path.with_suffix(raw_path.suffix + ".dvc")
    if pointer.exists():
        try:
            import yaml
            metadata = yaml.safe_load(pointer.read_text(encoding="utf-8"))
            return str(metadata["outs"][0].get("md5", "unknown"))
        except (KeyError, IndexError, TypeError, ValueError):
            pass
    import hashlib
    return hashlib.sha256(raw_path.read_bytes()).hexdigest()


def _git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "working-tree"


def _log_optional_shap(config: dict[str, Any], best: dict[str, Any], X_train: pd.DataFrame, client: MlflowClient) -> None:
    """Attempt a small SHAP summary for the selected run without breaking training."""
    if not config["models"]["shap_summary_enabled"]:
        return
    try:
        import matplotlib.pyplot as plt
        import shap

        columns = config["project"]["feature_columns"]
        sample = X_train.sample(
            n=min(config["models"]["shap_sample_size"], len(X_train)),
            random_state=config["data"]["random_seed"],
        )
        pipeline = mlflow.sklearn.load_model(
            f"runs:/{best['run_id']}/{config['registry']['model_artifact_path']}"
        )
        positive_index = list(pipeline.classes_).index(config["project"]["positive_class"])

        def predict(values):
            return pipeline.predict_proba(pd.DataFrame(values, columns=columns))[:, positive_index]

        background = sample.to_numpy()
        explainer = shap.Explainer(predict, shap.maskers.Independent(background), feature_names=columns)
        explanations = explainer(background, max_evals=2 * len(columns) + 1)
        shap.summary_plot(explanations, background, feature_names=columns, show=False)
        artifact_path = project_path(config["paths"]["mlflow_artifact_path"]) / f"shap-{best['run_id']}.png"
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(artifact_path, bbox_inches="tight")
        plt.close()
        client.log_artifact(best["run_id"], str(artifact_path), artifact_path="explainability")
    except Exception as exc:  # Optional by design: a SHAP incompatibility must not block model delivery.
        print(f"Optional SHAP summary was skipped: {exc}")


def train_models(config: dict[str, Any], input_path: Path) -> dict[str, Any]:
    """Split once, fit each configured model, log artifacts, register versions."""
    frame = pd.read_csv(input_path)
    project = config["project"]
    columns = project["feature_columns"]
    target = project["target_column"]
    positive_class = project["positive_class"]
    data = config["data"]
    X_train, X_test, y_train, y_test = train_test_split(
        frame[columns], frame[target], test_size=data["test_size"],
        random_state=data["random_seed"], stratify=frame[target],
    )
    train_path = project_path(data["train_path"])
    test_path = project_path(data["test_path"])
    train_path.parent.mkdir(parents=True, exist_ok=True)
    pd.concat([X_train, y_train], axis=1).to_csv(train_path, index=False)
    pd.concat([X_test, y_test], axis=1).to_csv(test_path, index=False)
    positive_weight = float((y_train != positive_class).sum() / max((y_train == positive_class).sum(), 1))

    registry = config["registry"]
    mlflow.set_tracking_uri(registry["tracking_uri"])
    mlflow.set_experiment(registry["experiment_name"])
    client = MlflowClient(tracking_uri=registry["tracking_uri"])
    data_version = _data_version(config)
    git_commit = _git_commit()
    results: list[dict[str, Any]] = []
    for model_key in config["models"]["selected"]:
        pipeline = build_pipeline(config, model_key, positive_weight)
        with mlflow.start_run(run_name=model_key) as run:
            mlflow.log_params({
                "model_key": model_key,
                "test_size": data["test_size"],
                "random_seed": data["random_seed"],
                "positive_class_weight": positive_weight,
                **{f"model.{key}": value for key, value in config["models"][model_key]["parameters"].items()},
            })
            pipeline.fit(X_train, y_train)
            positive_index = list(pipeline.classes_).index(positive_class)
            probabilities = pipeline.predict_proba(X_test)[:, positive_index]
            binary_y_test = (y_test.to_numpy() == positive_class).astype(int)
            scores = classification_metrics(binary_y_test, probabilities, config["models"]["decision_threshold"])
            logged = {key: value for key, value in scores.items() if isinstance(value, float | int)}
            mlflow.log_metrics(logged)
            mlflow.set_tags({"data_version": data_version, "git_commit": git_commit, "model_key": model_key})
            artifact_dir = project_path(config["paths"]["mlflow_artifact_path"]) / run.info.run_id
            log_evaluation_artifacts(scores, artifact_dir, config["paths"])
            mlflow.log_artifacts(
                str(artifact_dir), artifact_path=registry["training_evaluation_artifact_path"]
            )
            model_info = mlflow.sklearn.log_model(
                pipeline,
                artifact_path=registry["model_artifact_path"],
                input_example=X_train.head(),
            )
            registered = mlflow.register_model(model_info.model_uri, registry["model_name"])
            client.set_model_version_tag(registry["model_name"], registered.version, registry["selection_metric"], str(logged[registry["selection_metric"]]))
            client.set_model_version_tag(registry["model_name"], registered.version, "run_id", run.info.run_id)
            client.set_model_version_tag(registry["model_name"], registered.version, "data_version", data_version)
            client.set_model_version_tag(registry["model_name"], registered.version, "git_commit", git_commit)
            result = {"model_key": model_key, "run_id": run.info.run_id, "version": str(registered.version), "metrics": logged}
            results.append(result)
            print(f"Logged {model_key}: {registry['selection_metric']}={logged[registry['selection_metric']]:.5f}; registry version={registered.version}")

    metric = registry["selection_metric"]
    best = max(results, key=lambda result: result["metrics"][metric])
    _log_optional_shap(config, best, X_train, client)
    summary = {
        "selection_metric": metric,
        "best_run_id": best["run_id"],
        "best_model_key": best["model_key"],
        "best_version": best["version"],
        "data_version": data_version,
        "git_commit": git_commit,
        "versions": results,
    }
    summary_path = project_path(config["paths"]["training_summary_path"])
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", default=None)
    args = parser.parse_args()
    config = load_config()
    train_models(config, project_path(args.input or config["data"]["processed_path"]))


if __name__ == "__main__":
    main()
