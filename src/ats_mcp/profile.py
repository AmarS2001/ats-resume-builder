"""Load and validate profile.yaml into a Pydantic Profile model."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from .models import Profile

# Default profile.yaml lives at the project root (two levels up from this file).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def load_profile(path: Path | None = None) -> Profile:
    """Read *profile.yaml* and return a validated :class:`Profile`.

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
        data = yaml.safe_load(fh)

    return Profile.model_validate(data)
