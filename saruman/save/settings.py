from __future__ import annotations

import json
from pathlib import Path

from saruman.paths import savedir

_FILENAME = "settings.json"
_DEFAULTS: dict = {"music_volume": 6, "sfx_volume": 5, "fullscreen": False}

_current: dict | None = None


def _path() -> Path:
    return savedir() / _FILENAME


def get() -> dict:
    global _current
    if _current is None:
        _current = load()
    return _current


def load() -> dict:
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return {**_DEFAULTS, **data}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return dict(_DEFAULTS)


def save() -> None:
    try:
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(get(), f, indent=2)
    except OSError:
        pass
