# -*- coding: utf-8 -*-
"""Content of market scanning tab."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.ptxboa_functions import config_number_columns, remove_subregions
from ptxboa.api import PtxboaAPI


def content_market_scanning(api: PtxboaAPI, res_costs: pd.DataFrame) -> None:
    """Create content for the "market scanning" sheet.

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
**Market scanning: Get an overview of competing PTX BOA supply countries
 and potential demand countries.**

This sheet helps you to better evaluate your country's competitive position
 as well as your options on the emerging global H2 market.

            """
        )

    # get input data:
    input_data = api.get_input_data(st.session_state["scenario"])

    # filter shipping and pipeline distances:
    distances = input_data.loc[
        (input_data["parameter_code"].isin(["shipping distance", "pipeline distance"]))
        & (input_data["target_country_code"] == st.session_state["country"]),
        ["source_region_code", "parameter_code", "value"],
    ]
    distances = distances.pivot_table(
        index="source_region_code",
        columns="parameter_code",
        values="value",
        aggfunc="sum",
    )

    # merge costs and distances:
    df_plot = pd.DataFrame()
    df_plot["total costs"] = res_costs["Total"]
    df_plot = df_plot.merge(distances, left_index=True, right_index=True)

    # do not show subregions:
    df_plot = remove_subregions(api, df_plot, st.session_state["country"])

    # create plot:st.session_state
    [c1, c2] = st.columns([1, 5])
    with c1:
        # select which distance to show:
        selected_distance = st.radio(
            "Select parameter:",
            ["shipping distance", "pipeline distance"],
        )
    with c2:
        fig = px.scatter(
            df_plot,
            x=selected_distance,
            y="total costs",
            title="Costs and transportation distances",
            height=600,
        )
        # Add text above markers
        fig.update_traces(
            text=df_plot.index,
            textposition="top center",
            mode="markers+text",
        )

        st.plotly_chart(fig)

    # show data in tabular form:
    st.markdown("**Data:**")
    column_config = config_number_columns(df_plot, format="%.1f")
    st.dataframe(df_plot, use_container_width=True, column_config=column_config)
