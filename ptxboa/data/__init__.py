# -*- coding: utf-8 -*-
"""Data files and code to load them."""

from os.path import dirname

import pandas as pd

DATA_DIR = dirname(__file__)


def load_data(name: str) -> pd.DataFrame:
    filepath = f"{DATA_DIR}/{name}.csv"
    return pd.read_csv(filepath)
