import sys
from pathlib import Path

import platformdirs


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent / "_internal"
    return Path(__file__).parent.parent


def asset_path(*parts: str) -> Path:
    return _root() / "assets" / Path(*parts)


def savedir() -> Path:
    d = Path(platformdirs.user_data_dir("ProjectSaruman", "ProjectSaruman"))
    d.mkdir(parents=True, exist_ok=True)
    return d
