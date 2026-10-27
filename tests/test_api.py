
import mlflow
import numpy as np
import pandas as pd
from fastapi.testclient import TestClient

from app import main
from src.config import load_config, project_path


class DummyClassifier:
    classes_ = [0, 1]

    def predict_proba(self, frame):
        return np.asarray([[0.7, 0.3] for _ in range(len(frame))])


def _payload() -> dict:
    config = load_config()
    row = pd.read_csv(project_path(config["testing"]["fixture_path"])).dropna(subset=config["project"]["feature_columns"]).iloc[0]
    return {name: row[name].item() if hasattr(row[name], "item") else row[name] for name in config["project"]["feature_columns"]}


def test_api_prediction_validation_info_and_reload(monkeypatch) -> None:
    main.STATE.update({"model": DummyClassifier(), "version": "7", "run_id": "run-7", "data_version": "data-7", "error": None})
    monkeypatch.setattr(main, "reload_model", lambda: {"status": "test-loaded"})
    config = load_config()
    monkeypatch.setitem(config["api"], "request_log_path", config["testing"]["api_log_path"])
    monkeypatch.setattr(main, "CONFIG", config)
    monkeypatch.setattr(main, "REGISTRY", config["registry"])
    with TestClient(main.app) as client:
        assert client.get(config["api"]["routes"]["health"]).json()["status"] == "ok"
        prediction = client.post(config["api"]["routes"]["predict"], json=_payload())
        assert prediction.status_code == 200
        assert 0 <= prediction.json()["default_probability"] <= 1
        assert "risk_band" in prediction.json()
        assert client.post(config["api"]["routes"]["batch"], json=[_payload()]).status_code == 200
        assert client.get(config["api"]["routes"]["model_info"]).json()["version"] == "7"
        invalid = _payload()
        invalid[config["data"]["age_column"]] = config["data"]["max_age"] + 1
        assert client.post(config["api"]["routes"]["predict"], json=invalid).status_code == 422

        class Version:
            version = "8"
            tags = {"run_id": "run-8", "data_version": "data-8"}

        class Client:
            def __init__(self, **kwargs):
                pass

            def get_model_version_by_alias(self, name, alias):
                return Version()

        monkeypatch.setattr(mlflow.sklearn, "load_model", lambda uri: DummyClassifier())
        monkeypatch.setattr(mlflow, "MlflowClient", Client)
        response = client.post(config["api"]["routes"]["reload"])
        assert response.status_code == 200
        assert response.json()["version"] == "8"
    assert project_path(config["api"]["request_log_path"]).exists()
