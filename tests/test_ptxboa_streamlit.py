# -*- coding: utf-8 -*-
"""Tests for the streamlit app."""
import pytest
from streamlit.testing.v1 import AppTest


@pytest.fixture
def running_app():
    """Fixture that returns a fresh instance of a running app."""
    at = AppTest.from_file("ptxboa_streamlit.py")
    at.run(timeout=20)
    return at


def test_app_smoke(running_app):
    """Test if the app starts up without errors."""
    assert not running_app.exception
