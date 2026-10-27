from pathlib import Path

import pandas as pd

from src.config import load_config, project_path
from src.prepare import prepare_data


def test_cleaning_deduplicates_filters_and_keeps_missing_values(tmp_path: Path) -> None:
    config = load_config()
    source = pd.read_csv(project_path(config["testing"]["fixture_path"]))
    valid = source.dropna(subset=config["project"]["feature_columns"]).iloc[0].copy()
    age_col = config["data"]["age_column"]
    emp_col = config["data"]["employment_length_column"]
    valid[age_col] = 30
    valid[emp_col] = None
    duplicate = valid.copy()
    invalid_age = valid.copy()
    invalid_age[age_col] = config["data"]["max_age"] + 1
    invalid_employment = valid.copy()
    invalid_employment[emp_col] = 20
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "clean.csv"
    pd.DataFrame([valid, duplicate, invalid_age, invalid_employment]).to_csv(input_path, index=False)

    cleaned = prepare_data(input_path, output_path, config)

    assert len(cleaned) == 1
    assert cleaned[emp_col].isna().all()
    assert output_path.exists()
