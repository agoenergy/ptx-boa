"""Utility functions for streamlit app runtime."""

import os
from typing import Literal


def get_app_mode() -> Literal["prod", "preview", "dev"]:
    ALLOWED_MODES = {"prod", "preview", "dev"}
    DEFAULT_MODE = "prod"

    app_mode = os.getenv("PTXBOA_MODE", DEFAULT_MODE).lower()

    if app_mode not in ALLOWED_MODES:
        allowed = ", ".join(sorted(ALLOWED_MODES))
        raise ValueError(f"Invalid PTXBOA_MODE='{app_mode}'. Allowed values: {allowed}")

    return app_mode  # type: ignore
