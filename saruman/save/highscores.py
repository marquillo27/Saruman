from __future__ import annotations

import json
from pathlib import Path

from saruman.config import TOP_SCORES
from saruman.paths import savedir

_FILENAME = "highscores.json"


def _path() -> Path:
    return savedir() / _FILENAME


def load() -> list[dict]:
    try:
        with open(_path(), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data[:TOP_SCORES]
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        pass
    return []


def save(entries: list[dict]) -> None:
    try:
        with open(_path(), "w", encoding="utf-8") as f:
            json.dump(entries, f, indent=2)
    except OSError:
        pass


def is_high_score(score: int, entries: list[dict]) -> bool:
    if score <= 0:
        return False
    if len(entries) < TOP_SCORES:
        return True
    return score > min(e["score"] for e in entries)


def clear() -> None:
    """Wipe the high-score table by saving an empty list."""
    save([])


def insert(name: str, score: int, entries: list[dict]) -> tuple[list[dict], int]:
    """Insert entry into top-10. Returns (sorted list, 1-based rank). rank is
    len+1 if the score didn't make the cut (shouldn't happen after is_high_score)."""
    new_entry = {"name": name.strip() or "???", "score": score}
    all_entries = list(entries) + [new_entry]
    all_entries.sort(key=lambda e: e["score"], reverse=True)
    all_entries = all_entries[:TOP_SCORES]
    try:
        rank = next(i + 1 for i, e in enumerate(all_entries) if e is new_entry)
    except StopIteration:
        rank = TOP_SCORES + 1
    return all_entries, rank
