# -*- coding: utf-8 -*-
"""Content of input data tab."""
import plotly.express as px
import streamlit as st

from app.plot_functions import plot_input_data_on_map
from app.ptxboa_functions import display_and_edit_input_data, read_markdown_file
from ptxboa.api import PtxboaAPI


def content_input_data(api: PtxboaAPI) -> None:
    """Create content for the "input data" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(read_markdown_file("md/whatisthis_input_data.md"))

    with st.container(border=True):
        st.subheader("Region specific data")

        data_selection = st.radio(
            "Select data type",
            ["CAPEX", "full load hours", "interest rate"],
            horizontal=True,
        )

        # in order to keep the figures horizontally aligned, we create two st.columns
        # pairs the columns are identified by c_{row}_{column}, zero indexed
        c_0_0, c_0_1 = st.columns([2, 1], gap="large")
        c_1_0, c_1_1 = st.columns([2, 1], gap="large")
        with c_0_0:
            st.markdown("**Map**")
            if data_selection in ["full load hours", "CAPEX"]:
                map_parameter = st.selectbox(
                    "Show Parameter on Map",
                    [
                        "Wind Onshore",
                        "Wind Offshore",
                        "PV tilted",
                        "Wind-PV-Hybrid",
                    ],
                    key="input_data_map_parameter",
                )
            else:
                map_parameter = "interest rate"
        with c_1_0:
            fig = plot_input_data_on_map(
                api=api,
                data_type=data_selection,
                color_col=map_parameter,
                scope="world",
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("**Data**"):
            df = display_and_edit_input_data(
                api,
                data_type=data_selection,
                scope="world",
                key=f"input_data_editor_{data_selection}",
            )
        with c_0_1:
            st.markdown("**Regional Distribution**")
        with c_1_1:
            # create plot:
            fig = px.box(df)
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.subheader("Data that is identical for all regions")

        st.markdown("**Conversion processes:**")
        with st.expander("**Data**"):
            display_and_edit_input_data(
                api,
                data_type="conversion_processes",
                scope=None,
                key="input_data_editor_conversion_processes",
            )
        st.markdown("**Transportation (ships and pipelines):**")
        with st.expander("**Data**"):
            display_and_edit_input_data(
                api,
                data_type="transportation_processes",
                scope=None,
                key="input_data_editor_transportation_processes",
            )
        st.markdown("**Transportation (compression, liquefication and reconversion):**")
        with st.expander("**Data**"):
            display_and_edit_input_data(
                api,
                data_type="reconversion_processes",
                scope=None,
                key="input_data_editor_reconversion_processes",
            )
