# -*- coding: utf-8 -*-
"""Content of compare costs tab."""
import pandas as pd
import streamlit as st

from app.plot_functions import create_bar_chart_costs
from app.ptxboa_functions import config_number_columns, remove_subregions
from ptxboa.api import PtxboaAPI


def display_costs(df_costs: pd.DataFrame, key: str, titlestring: str):
    """Display costs as table and bar chart."""
    st.subheader(titlestring)
    c1, c2 = st.columns([1, 5])
    with c1:
        # filter data:
        df_res = df_costs.copy()

        # select filter:
        show_which_data = st.radio(
            "Select elements to display:",
            ["All", "Manual select"],
            index=0,
            key=f"show_which_data_{key}",
        )

        # apply filter:
        if show_which_data == "Manual select":
            ind_select = st.multiselect(
                "Select regions:",
                df_res.index.values,
                default=df_res.index.values,
                key=f"select_data_{key}",
            )
            df_res = df_res.loc[ind_select]

        # sort:
        sort_ascending = st.toggle(
            "Sort by total costs?", value=True, key=f"sort_data_{key}"
        )
        if sort_ascending:
            df_res = df_res.sort_values(["Total"], ascending=True)
    with c2:
        # create graph:
        fig = create_bar_chart_costs(
            df_res,
            current_selection=st.session_state[key],
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("**Data**"):
        column_config = config_number_columns(
            df_res, format=f"%.1f {st.session_state['output_unit']}"
        )
        st.dataframe(df_res, use_container_width=True, column_config=column_config)


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
