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
                    "Show parameter on map",
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
                key=f"input_data_{data_selection}",
            )
        with c_0_1:
            st.markdown("**Regional distribution**")
        with c_1_1:
            # create plot:
            fig = px.box(df)
            fig.update_layout(xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)

    with st.container(border=True):
        st.subheader("Global data")
        with st.expander("**Electricity generation**"):
            display_and_edit_input_data(
                api,
                data_type="electricity_generation",
                scope=None,
                key="input_data_electricity_generation",
            )
        with st.expander("**Electrolysis and derivate production**"):
            display_and_edit_input_data(
                api,
                data_type="conversion_processes",
                scope=None,
                key="input_data_conversion_processes",
            )
        with st.expander("**Transportation (ships and pipelines)**"):
            display_and_edit_input_data(
                api,
                data_type="transportation_processes",
                scope=None,
                key="input_data_transportation_processes",
            )
        with st.expander(
            "**Transportation (compression, liquefication and reconversion)**"
        ):
            display_and_edit_input_data(
                api,
                data_type="reconversion_processes",
                scope=None,
                key="input_data_reconversion_processes",
            )
        with st.expander("**Specific costs for materials and energy carriers**"):
            display_and_edit_input_data(
                api,
                data_type="specific_costs",
                scope=None,
                key="input_data_specific_costs",
            )
