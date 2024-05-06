# -*- coding: utf-8 -*-
"""Common Paths and settings."""
import logging
import os
from pathlib import Path

IS_TEST = "PYTEST_CURRENT_TEST" in os.environ  # TODO unused
KEY_SEPARATOR = ","

# PATHS
_THIS_DIR = Path(__file__).parent.resolve()

PROFILES_DIR = _THIS_DIR / ".." / "flh_opt" / "renewable_profiles"
STATIC_DATA_DIR = _THIS_DIR / "static"
DEFAULT_CACHE_DIR = Path(os.environ.get("PTXBOA_CACHE_DIR") or _THIS_DIR / "cache")
DEFAULT_DATA_DIR = _THIS_DIR / "data"


logger = logging.getLogger()
