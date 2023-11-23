# -*- coding: utf-8 -*-
"""Content of compare costs tab."""
import pandas as pd
import streamlit as st

from app.layout_elements import display_costs
from app.ptxboa_functions import remove_subregions
from ptxboa.api import PtxboaAPI


def content_compare_costs(
    api: PtxboaAPI,
    costs_per_region: pd.DataFrame,
    costs_per_scenario: pd.DataFrame,
    costs_per_res_gen: pd.DataFrame,
    costs_per_chain: pd.DataFrame,
) -> None:
    """Create content for the "compare costs" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Compare costs**

On this sheet, users can analyze total cost and cost components for
different supply countries, scenarios, renewable electricity sources and process chains.
Data is represented as a bar chart and in tabular form.

Data can be filterend and sorted.
            """
        )

    display_costs(
        remove_subregions(api, costs_per_region, st.session_state["country"]),
        "region",
        "Costs by region:",
    )

    display_costs(costs_per_scenario, "scenario", "Costs by data scenario:")

    display_costs(
        costs_per_res_gen, "res_gen", "Costs by renewable electricity source:"
    )

    display_costs(costs_per_chain, "chain", "Costs by supply chain:")
