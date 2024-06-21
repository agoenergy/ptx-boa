# -*- coding: utf-8 -*-
"""Content of input data tab."""
import plotly.express as px
import streamlit as st

from app.layout_elements import display_and_edit_input_data, what_is_a_boxplot
from app.plot_functions import plot_input_data_on_map
from app.ptxboa_functions import read_markdown_file
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
    with st.popover("*Help*", use_container_width=True):
        st.markdown(
            read_markdown_file("md/whatisthis_input_data.md"), unsafe_allow_html=True
        )

    with st.container(border=True):
        st.subheader("Region specific data")

        data_selection = st.radio(
            "Select data type",
            ["CAPEX", "full load hours", "WACC"],
            horizontal=True,
        )

        with st.expander("**Map**", expanded=True):

            if data_selection in ["full load hours", "CAPEX"]:
                if data_selection == "full load hours":
                    select_options = [
                        "Wind Onshore",
                        "Wind Offshore",
                        "PV tilted",
                        "Wind Onshore (hybrid)",
                        "PV tilted (hybrid)",
                    ]
                if data_selection == "CAPEX":
                    select_options = [
                        "Wind Onshore",
                        "Wind Offshore",
                        "PV tilted",
                    ]

                map_parameter = st.selectbox(
                    "Select parameter to display on map:",
                    select_options,
                    key="input_data_map_parameter",
                )
            else:
                map_parameter = "WACC"
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
        with st.expander("**Regional distribution**"):
            # create plot:
            if data_selection == "CAPEX":
                ylabel = "CAPEX (USD/kW)"
                hover_name = "process_code"
            if data_selection == "full load hours":
                ylabel = "full load hours (h/a)"
                hover_name = "res_gen"
            if data_selection == "WACC":
                ylabel = "WACC (%)"
                hover_name = "parameter_code"
            fig = px.box(
                df,
                hover_data=[df.index],
                hover_name=hover_name,
            )
            fig.update_layout(xaxis_title=None, yaxis_title=ylabel)
            st.plotly_chart(fig, use_container_width=True)
            what_is_a_boxplot()

    with st.container(border=True):
        st.subheader("Global data")
        with st.expander("**Electricity generation**"):
            display_and_edit_input_data(
                api,
                data_type="electricity_generation",
                scope=None,
                key="input_data_electricity_generation",
            )
        with st.expander("**Electrolysis and derivative production**"):
            st.caption(
                (
                    "The unit of CAPEX and OPEX (fix) is USD/t for Green iron "
                    "reduction and USD/MW for all other processes."
                )
            )
            display_and_edit_input_data(
                api,
                data_type="conversion_processes",
                scope=None,
                key="input_data_conversion_processes",
            )
        with st.expander("**Storage**"):
            st.caption(
                (
                    "- Storage CAPEX are defined per charging power.\n"
                    "- Efficiencies are round-trip.\n"
                    "- Time-dependent losses are neglected.\n"
                    "- For electricity storage (batteries) we assume a fixed ratio of 4"
                    " MWh storage capacity per MW charging power\n"
                    " and equal charging/discharging power.\n"
                    "- For hydrogen storage (tanks) we assume storage capacity and"
                    " discharge power to be non-binding because the comporessor is by"
                    " far the most expensive component."
                )
            )
            display_and_edit_input_data(
                api,
                data_type="storage",
                scope=None,
                key="input_data_storage",
            )

        with st.expander("**Transportation (ships and pipelines)**"):
            st.caption(
                (
                    "The unit of levelized costs is USD/(t km) for Green iron ship "
                    "(bunker fuel consumption) and USD/(kW km) for all other "
                    "processes."
                )
            )
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
        with st.expander("**Direct air capture and desalination**"):
            st.caption(
                (
                    "Units for CAPEX and OPEX (fix) are per kg of CO₂ for "
                    "direct air capture and per kg of H₂0 for sea water "
                    "desalination, respectively."
                ),
                unsafe_allow_html=True,
            )
            display_and_edit_input_data(
                api,
                data_type="dac_and_desalination",
                scope=None,
                key="input_data_dac_and_desalination",
            )
        with st.expander("**Specific costs for materials and energy carriers**"):
            display_and_edit_input_data(
                api,
                data_type="specific_costs",
                scope=None,
                key="input_data_specific_costs",
            )
        with st.expander("**Conversion coefficients**"):
            st.caption(
                read_markdown_file("md/info_conversion_coefficients.md"),
                unsafe_allow_html=True,
            )
            display_and_edit_input_data(
                api,
                data_type="conversion_coefficients",
                scope=None,
                key="input_data_conversion_coefficients",
            )
