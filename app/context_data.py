# -*- coding: utf-8 -*-
"""Module for loading context data."""
import pandas as pd
import streamlit as st


@st.cache_data()
def load_context_data():
    """Import context data from excel file."""
    filename = "data/context_data.xlsx"
    cd = {}
    cd["demand_countries"] = pd.read_excel(
        filename, sheet_name="demand_countries", skiprows=1
    )
    cd["certification_schemes_countries"] = pd.read_excel(
        filename, sheet_name="certification_schemes_countries"
    )
    cd["certification_schemes"] = pd.read_excel(
        filename, sheet_name="certification_schemes", skiprows=1
    )
    cd["sustainability"] = pd.read_excel(filename, sheet_name="sustainability")
    cd["supply"] = pd.read_excel(filename, sheet_name="supply", skiprows=1)
    cd["literature"] = pd.read_excel(filename, sheet_name="literature")
    cd["infobox"] = pd.read_excel(
        filename,
        sheet_name="infobox",
        usecols="A:F",
        skiprows=1,
    ).set_index("country_name")
    return cd
