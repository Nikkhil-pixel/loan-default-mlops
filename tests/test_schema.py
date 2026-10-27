import pandas as pd
import pytest
from pydantic import ValidationError

from app.schemas import build_request_model
from src.config import load_config, project_path


def _valid_payload() -> dict:
    config = load_config()
    row = pd.read_csv(project_path(config["testing"]["fixture_path"])).dropna(subset=config["project"]["feature_columns"]).iloc[0]
    return {name: row[name].item() if hasattr(row[name], "item") else row[name] for name in config["project"]["feature_columns"]}


def test_schema_accepts_known_record_and_rejects_invalid_values() -> None:
    config = load_config()
    request_model = build_request_model(config)
    payload = _valid_payload()
    assert request_model(**payload)
    age = config["data"]["age_column"]
    payload[age] = config["data"]["max_age"] + 1
    with pytest.raises(ValidationError):
        request_model(**payload)
    payload = _valid_payload()
    category_column = config["project"]["categorical_features"][0]
    payload[category_column] = "UNCONFIGURED"
    with pytest.raises(ValidationError):
        request_model(**payload)
    payload = _valid_payload()
    payload["unexpected_field"] = 1
    with pytest.raises(ValidationError):
        request_model(**payload)
