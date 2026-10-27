"""Shared configuration loader for the pipeline and prediction service."""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_FILE = os.getenv("PARAMS_FILE", "params.yaml")
_ENV_PATTERN = re.compile(r"\$\{([^}:]+)(?::-([^}]*))?\}")


def _interpolate(value: Any) -> Any:
    """Expand environment placeholders recursively, including nested defaults."""
    if isinstance(value, dict):
        return {key: _interpolate(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_interpolate(item) for item in value]
    if isinstance(value, str):
        previous = None
        while value != previous:
            previous = value
            value = _ENV_PATTERN.sub(lambda match: os.getenv(match.group(1), match.group(2) or ""), value)
        return value
    return value


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load YAML parameters and expand environment-based overrides."""
    config_path = Path(path) if path else Path(DEFAULT_CONFIG_FILE)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    with config_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    return _interpolate(config)


def project_path(value: str | Path) -> Path:
    """Resolve a configured project path against the repository root."""
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def config_hash(path: str | Path | None = None) -> str:
    """Return a stable hash of the active configuration file."""
    import hashlib

    config_path = Path(path) if path else Path(DEFAULT_CONFIG_FILE)
    if not config_path.is_absolute():
        config_path = ROOT / config_path
    return hashlib.sha256(config_path.read_bytes()).hexdigest()
