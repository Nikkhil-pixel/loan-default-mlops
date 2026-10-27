import re

from src.config import ROOT, load_config


def _configured_values(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key
            yield from _configured_values(item)
    elif isinstance(value, list):
        yield from value
    else:
        yield value


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
    known_values.update(config["project"]["categories"].keys())
    for choices in config["project"]["categories"].values():
        known_values.update(choice for choice in choices if len(choice) > 2)
    for section in ("data", "api", "monitoring", "paths", "registry"):
        known_values.update(
            value for value in _configured_values(config[section])
            if isinstance(value, str) and ("/" in value or "://" in value or "." in value)
        )
    numeric_values = {
        value for value in _configured_values(config)
        if isinstance(value, int | float) and not isinstance(value, bool) and value not in {0, 1, 2, 3, 4, 5}
    }
    for value in known_values:
        if value:
            assert str(value) not in source_text, f"Tunable value {value!r} appears as a source-code literal."
    for value in numeric_values:
        literal = str(value)
        assert not re.search(rf"(?<![\w.]){re.escape(literal)}(?![\w.])", source_text), (
            f"Configured numeric value {literal!r} appears as a hard-coded source literal."
        )
