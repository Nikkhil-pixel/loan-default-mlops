from pathlib import Path

from mlflow import MlflowClient

from src.config import load_config
from src.promote import promote_model


def test_first_version_promotes_and_weaker_version_stays_challenger(tmp_path: Path) -> None:
    config = load_config()
    database = tmp_path / "registry.db"
    config["registry"]["tracking_uri"] = f"sqlite:///{database}"
    name = config["registry"]["model_name"]
    client = MlflowClient(tracking_uri=config["registry"]["tracking_uri"])
    client.create_registered_model(name)
    first = client.create_model_version(name, source="file:///candidate-one", run_id="run-one")
    client.set_model_version_tag(name, first.version, config["registry"]["selection_metric"], "0.81")
    first_result = promote_model(config)
    assert first_result["decision"] == "promoted"
    assert client.get_model_version_by_alias(name, config["registry"]["champion_alias"]).version == first.version

    second = client.create_model_version(name, source="file:///candidate-two", run_id="run-two")
    client.set_model_version_tag(name, second.version, config["registry"]["selection_metric"], "0.80")
    second_result = promote_model(config)
    assert second_result["decision"] == "challenger"
    assert client.get_model_version_by_alias(name, config["registry"]["challenger_alias"]).version == second.version
