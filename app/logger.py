"""Simple thread-safe JSON Lines logging for model-serving observations."""
from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_LOCK = threading.Lock()


def log_prediction(path: Path, record: dict[str, Any]) -> None:
    """Append one compact JSON record, creating the configured parent directory."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"timestamp": datetime.now(UTC).isoformat(), **record}
    with _LOCK, path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, allow_nan=False) + "\n")
