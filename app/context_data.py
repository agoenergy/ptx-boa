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
        filename, sheet_name="demand_countries", skiprows=1, keep_default_na=False
    )
    cd["certification_schemes"] = pd.read_excel(
        filename, sheet_name="certification_schemes", skiprows=1, keep_default_na=False
    )
    cd["sustainability"] = pd.read_excel(filename, sheet_name="sustainability")
    cd["supply"] = pd.read_excel(
        filename, sheet_name="supply", skiprows=1, keep_default_na=False
    )
    cd["literature"] = pd.read_excel(filename, sheet_name="literature")

    return _insert_clickable_references(cd)


def _insert_clickable_references(context_data):
    """Insert clickable markdown references into the context data text fields."""
    literature = context_data["literature"]
    literature["markdown_link"] = (
        "[" + literature["short_name"] + "](" + literature["url"] + ")"
    )
    links = literature.set_index("short_name")["markdown_link"].to_dict()

    cd_new = {}
    cd_new["literature"] = context_data["literature"]
    for sheet in [
        "demand_countries",
        "certification_schemes",
        "sustainability",
        "supply",
    ]:
        for ref, link in links.items():
            if isinstance(link, str):
                df = context_data[sheet]
                for col in df.columns:
                    df[col] = df[col].astype(str).str.replace(ref, link)

        cd_new[sheet] = df

    return cd_new
