# -*- coding: utf-8 -*-
"""Data files and code to load them."""

from os.path import dirname

import pandas as pd

DATA_DIR = dirname(__file__)


def load_data(name: str) -> pd.DataFrame:
    filepath = f"{DATA_DIR}/{name}.csv"
    return pd.read_csv(filepath)


def load_context_data(name: str) -> pd.DataFrame:
    """This is just a mockup, eventually, we won't be reading from xlsx."""
    filepath = f"{DATA_DIR}/context_data.xlsx"

    if name == "context_cs_countries":
        return pd.read_excel(
            filepath,
            sheet_name="context_cs_countries",
            true_values=["yes"],
            false_values=["no"],
        ).set_index("REGULATION OR STANDARD")
    elif name == "context_cs_scope":
        return pd.read_excel(
            filepath,
            sheet_name="context_cs_scope",
        ).set_index("REGULATION OR STANDARD")
    elif name == "_context_data_infobox":
        return pd.read_excel(
            filepath,
            sheet_name="_context_data_infobox",
            usecols="A:F",
            skiprows=1,
        ).set_index("country_name")
    else:
        KeyError(name)
