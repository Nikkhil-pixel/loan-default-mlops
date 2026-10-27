
from src.config import ROOT, load_config


def test_known_tunable_values_are_not_embedded_in_src_or_app() -> None:
    config = load_config()
    source_text = "\n".join(
        path.read_text(encoding="utf-8")
        for folder in (ROOT / "src", ROOT / "app")
        for path in folder.rglob("*.py")
    )
    known_values = set(config["project"]["feature_columns"])
    known_values.update([config["project"]["target_column"], config["registry"]["model_name"]])
    known_values.update(config["models"]["selected"])
    known_values.update(config["api"]["routes"].values())
    known_values.update([config["data"]["raw_path"], config["data"]["processed_path"], config["registry"]["tracking_uri"]])
    for value in known_values:
        assert value not in source_text, f"Tunable value {value!r} appears as a source-code literal."
