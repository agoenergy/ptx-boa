# -*- coding: utf-8 -*-
"""Data files and code to load them."""

from os.path import dirname

import pandas as pd

DATA_DIR = dirname(__file__)


def load_data(name: str) -> pd.DataFrame:
    filepath = f"{DATA_DIR}/{name}.csv"
    df = pd.read_csv(filepath)
    # numerical columns should never be empty, dimension columns
    # maybe empty and will be filled with ""
    df = df.fillna("")
    return df
