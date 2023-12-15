# -*- coding: utf-8 -*-
"""Content of input data tab."""
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_antd_components import SegmentedItem, segmented

from app.layout_elements import display_costs
from app.plot_functions import plot_costs_on_map, plot_input_data_on_map
from app.ptxboa_functions import (
    display_and_edit_input_data,
    read_markdown_file,
    select_subregions,
)
from ptxboa.api import PtxboaAPI


def content_deep_dive_countries(
    api: PtxboaAPI,
    costs_per_region: pd.DataFrame,
    costs_per_region_without_user_changes: pd.DataFrame,
) -> None:
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
        st.markdown(read_markdown_file("md/whatisthis_deep_dive_countries.md"))

    st.write("Select which country to display:")
    ddc = segmented(
        items=[
            SegmentedItem(label="Argentina"),
            SegmentedItem(label="Morocco"),
            SegmentedItem(label="South Africa"),
        ],
        grow=True,
    )

    with st.container(border=True):
        st.subheader("Costs per subregion")
        fig_map = plot_costs_on_map(
            api, costs_per_region, scope=ddc, cost_component="Total"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.divider()

        display_costs(
            select_subregions(costs_per_region, ddc),
            select_subregions(costs_per_region_without_user_changes, ddc),
            key="region",
            titlestring="Costs per subregion",
            key_suffix=ddc,
        )

    with st.container(border=True):
        st.subheader("Full load hours of renewable generation")

        # in order to keep the figures horizontally aligned, we create two st.columns
        # pairs, the columns are identified by c_{row}_{column}, zero indexed
        c_0_0, c_0_1 = st.columns([2, 1], gap="large")
        c_1_0, c_1_1 = st.columns([2, 1], gap="large")
        with c_0_0:
            st.markdown("**Map**")
            map_parameter = st.selectbox(
                "Show parameter on map",
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
                key=f"input_data_full_load_hours_{ddc.replace(' ', '_').lower()}",
            )

        with c_0_1:
            st.markdown("**Regional distribution**")
        with c_1_1:
            fig = px.box(df)
            fig.update_layout(xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
