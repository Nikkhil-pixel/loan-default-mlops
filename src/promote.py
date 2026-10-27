"""Choose a champion model version with an explicit metric-based guardrail."""
from __future__ import annotations

import argparse
import json
from typing import Any

import mlflow
from mlflow import MlflowClient
from mlflow.exceptions import MlflowException

from src.config import load_config, project_path


def promote_model(
    config: dict[str, Any],
    requested_version: str | None = None,
    candidate_versions: list[str] | None = None,
) -> dict[str, Any]:
    """Compare a new registry version with the current champion and set aliases."""
    registry = config["registry"]
    mlflow.set_tracking_uri(registry["tracking_uri"])
    client = MlflowClient(tracking_uri=registry["tracking_uri"])
    model_name = registry["model_name"]
    metric = registry["selection_metric"]
    all_versions = list(client.search_model_versions(f"name='{model_name}'"))
    if not all_versions:
        raise ValueError(f"No registered versions exist for configured model {model_name!r}.")
    try:
        champion = client.get_model_version_by_alias(model_name, registry["champion_alias"])
    except MlflowException:
        champion = None

    available = all_versions
    if candidate_versions is not None:
        allowed = {str(value) for value in candidate_versions}
        available = [version for version in available if str(version.version) in allowed]
    candidates = [version for version in available if champion is None or str(version.version) != str(champion.version)]
    if requested_version is not None:
        candidates = [version for version in candidates if str(version.version) == str(requested_version)]
        if not candidates:
            raise ValueError(f"Requested version {requested_version!r} is not an available challenger from the current training run.")
    candidates = [version for version in candidates if metric in version.tags]
    if not candidates:
        if champion is not None:
            return {"decision": "unchanged", "reason": "No unpromoted candidate has the configured metric.", "champion_version": champion.version}
        raise ValueError("No candidate versions carry the configured promotion metric.")
    candidate = max(candidates, key=lambda version: float(version.tags[metric]))
    candidate_score = float(candidate.tags[metric])
    margin = float(registry["metric_promotion_margin"])
    if champion is None:
        client.set_registered_model_alias(model_name, registry["champion_alias"], candidate.version)
        decision = {"decision": "promoted", "reason": "First registered model; no champion existed.", "candidate_version": candidate.version, "candidate_score": candidate_score}
    else:
        champion_score = float(champion.tags[metric])
        direction = registry.get("metric_direction", "maximize")
        improvement = candidate_score - champion_score if direction == "maximize" else champion_score - candidate_score
        if improvement >= margin:
            client.set_registered_model_alias(model_name, registry["challenger_alias"], champion.version)
            client.set_registered_model_alias(model_name, registry["champion_alias"], candidate.version)
            decision = {"decision": "promoted", "reason": "Candidate met the configured improvement margin.", "candidate_version": candidate.version, "candidate_score": candidate_score, "previous_champion_version": champion.version, "previous_champion_score": champion_score, "improvement": improvement}
        else:
            client.set_registered_model_alias(model_name, registry["challenger_alias"], candidate.version)
            decision = {"decision": "challenger", "reason": "Candidate did not meet the configured improvement margin.", "candidate_version": candidate.version, "candidate_score": candidate_score, "champion_version": champion.version, "champion_score": champion_score, "improvement": improvement, "required_margin": margin}
    print(f"Promotion decision: {decision}")
    return decision


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", default=None, help="Optionally evaluate an exact model version.")
    args = parser.parse_args()
    config = load_config()
    summary_path = project_path(config["paths"]["training_summary_path"])
    versions = None
    if summary_path.exists():
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        versions = [item["version"] for item in summary.get("versions", [])]
    promote_model(config, args.version, versions)


if __name__ == "__main__":
    main()
