from __future__ import annotations

import json
import os
from pathlib import Path


def get_api_key() -> str:
    key = os.environ.get("SUPERNOTES_API_KEY")
    if key:
        return key

    config_path = Path.home() / ".config" / "supernotes" / "config.json"
    if config_path.exists():
        data = json.loads(config_path.read_text())
        key = data.get("api_key")
        if key:
            return key

    raise RuntimeError(
        "Supernotes API key not found. "
        "Set SUPERNOTES_API_KEY env var or run 'supernotes config set-key'."
    )


def save_api_key(key: str) -> None:
    config_dir = Path.home() / ".config" / "supernotes"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.json"

    data = {}
    if config_path.exists():
        data = json.loads(config_path.read_text())

    data["api_key"] = key
    config_path.write_text(json.dumps(data, indent=2))
