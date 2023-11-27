# -*- coding: utf-8 -*-
"""Content of input data tab."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.layout_elements import display_costs
from app.plot_functions import plot_costs_on_map, plot_input_data_on_map
from app.ptxboa_functions import display_and_edit_input_data, select_subregions
from ptxboa.api import PtxboaAPI


def content_deep_dive_countries(api: PtxboaAPI, costs_per_region: pd.DataFrame) -> None:
    """Create content for the "costs by region" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    costs_per_region : pd.DataFrame
        Results.

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Deep-dive countries: Data on country and regional level**

For the three deep-dive countries (Argentina, Morocco and South Africa)
this tab shows full load hours of renewable generation and total costs
in regional details.

The box plots show median, 1st and 3rd quartile as well as the total spread of values.
They also show the data for your selected supply country or region for comparison.
            """
        )

    ddc = st.radio(
        "Select country:", ["Argentina", "Morocco", "South Africa"], horizontal=True
    )

    fig_map = plot_costs_on_map(
        api, costs_per_region, scope=ddc, cost_component="Total"
    )
    st.plotly_chart(fig_map, use_container_width=True)

    display_costs(
        select_subregions(costs_per_region, ddc),
        key="region",
        titlestring="Costs per subregion",
        key_suffix=ddc,
    )

    st.subheader("Full load hours of renewable generation")

    # in order to keep the figures horizontally aligned, we create two st.columns pairs
    # the columns are identified by c_{row}_{column}, zero indexed
    c_0_0, c_0_1 = st.columns([2, 1], gap="large")
    c_1_0, c_1_1 = st.columns([2, 1], gap="large")
    with c_0_0:
        st.markdown("**Map**")
        map_parameter = st.selectbox(
            "Show Parameter on Map",
            [
                "Wind Onshore",
                "Wind Offshore",
                "PV tilted",
                "Wind-PV-Hybrid",
            ],
            key="ddc_flh_map_parameter",
        )
    with c_1_0:
        fig = plot_input_data_on_map(
            api=api,
            data_type="full load hours",
            color_col=map_parameter,
            scope=ddc,
        )
        st.plotly_chart(fig, use_container_width=True)
    with st.expander("**Data**"):
        df = display_and_edit_input_data(
            api,
            data_type="full load hours",
            scope=ddc,
            key="input_data_editor_full_load_hours_ddc",
        )

    with c_0_1:
        st.markdown("**Regional Distribution**")
    with c_1_1:
        fig = px.box(df)
        st.plotly_chart(fig, use_container_width=True)
