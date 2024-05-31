# -*- coding: utf-8 -*-
"""Common Paths and settings."""
import logging
import os
import warnings
from pathlib import Path

KEY_SEPARATOR = ","


# PATHS
_THIS_DIR = Path(__file__).parent.resolve()
PROFILES_DIR = _THIS_DIR / ".." / "flh_opt" / "renewable_profiles"
STATIC_DATA_DIR = _THIS_DIR / "static"
DEFAULT_CACHE_DIR = Path(os.environ.get("PTXBOA_CACHE_DIR") or _THIS_DIR / "cache")
DEFAULT_DATA_DIR = _THIS_DIR / "data"


logger = logging.getLogger()

warnings.filterwarnings(  # filter pandas warning from pypsa optimizer
    action="ignore",
    category=FutureWarning,
    message=(
        r".*A value is trying to be set on a copy of a DataFrame or Series "
        r"through chained assignment using an inplace method.*"
    ),
)
warnings.filterwarnings(  # filter DeprecationWarning for read network
    action="ignore",
    category=DeprecationWarning,
)
