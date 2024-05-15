# -*- coding: utf-8 -*-
"""Tests for the streamlit app."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def running_app():
    """Fixture that returns a fresh instance of a running app."""
    at = AppTest.from_file("ptxboa_streamlit.py")
    at.run(timeout=60)
    return at


def test_app_smoke(running_app):
    """Test if the app starts up without errors."""
    assert not running_app.exception


@pytest.fixture(
    params=(
        "Info",
        "Costs",
        "Market scanning",
        "Input data",
        "Deep-dive countries",
        "Country fact sheets",
        "Certification schemes",
        "Sustainability",
        "Literature",
        "Optimization",
    )
)
def running_app_on_tab(request):
    tab = request.param
    at = AppTest.from_file("ptxboa_streamlit.py")
    at.session_state["tab_key"] = "tab_key_0"
    at.session_state[at.session_state["tab_key"]] = tab
    at.run(timeout=60)
    return at


def test_tabs_smoke(running_app_on_tab):
    assert not running_app_on_tab.exception
