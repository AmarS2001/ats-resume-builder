"""Load profile.yaml directly into a dictionary."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

# Default profile.yaml lives at the project root (two levels up from this file).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_profile(path: Path | None = None) -> dict:
    """Read *profile.yaml* and return the raw parsed dictionary.

    Parameters
    ----------
    path:
        Explicit path to the YAML file. Falls back to
        ``ATS_PROFILE_PATH`` environment variable, then to
        ``<project_root>/profile.yaml`` when *None*.
    """
    if path is None:
        env_path = os.environ.get("ATS_PROFILE_PATH")
        if env_path:
            path = Path(env_path)
        else:
            path = _PROJECT_ROOT / "profile.yaml"

    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)
