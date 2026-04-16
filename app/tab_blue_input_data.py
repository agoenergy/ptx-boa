"""Content of blue input data tab."""

from typing import Literal

import streamlit as st

from app.layout_elements import display_and_edit_input_data
from app.plot_functions import plot_input_data_on_map
from app.ptxboa_functions import read_markdown_file
from ptxboa.api import PtxboaAPI


def content_input_data(api: PtxboaAPI) -> None:
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file("md/tab_blue_input_data/whatisthis_blue_input_data.md"),
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        st.subheader("Region specific data")

        data_selection: Literal[
            "WACC",
            "Natural gas production costs",
            "Natural gas production losses",
            "Natural gas price",
        ] = st.selectbox(
            "Select data type",
            [
                "WACC",
                "Natural gas production costs",
                "Natural gas production losses",
                "Natural gas price",
            ],
        )

        with st.expander("**Map**", expanded=True):
            map_parameter = {
                "Natural gas price": "specific costs",
                "Natural gas production costs": "OPEX (other variable)",
                "Natural gas production losses": "losses (own fuel)",
            }.get(data_selection, data_selection)
            fig = plot_input_data_on_map(
                api=api,
                data_type=data_selection,
                color_col=map_parameter,
                scope="world",
                tool_version_color="blue",
            )
            st.plotly_chart(fig, width="stretch")

        with st.expander("**Data**"):
            display_and_edit_input_data(
                api,
                data_type=data_selection,
                scope="world",
                key=f"input_data_{data_selection}",
                tool_version_color="blue",
            )

    with st.container(border=True):
        st.subheader("Global data")
        with st.expander("**Conversion**"):
            display_and_edit_input_data(
                api,
                data_type="conversion_processes",
                scope=None,
                key="input_data_conversion_processes",
                tool_version_color="blue",
            )

        with st.expander("**Transportation (ships and pipelines)**"):
            st.caption(
                read_markdown_file(
                    "md/tab_blue_input_data/description_transportation.md"
                )
            )
            display_and_edit_input_data(
                api,
                data_type="transportation_processes",
                scope=None,
                key="input_data_transportation_processes",
                tool_version_color="blue",
            )
        with st.expander(
            "**Transportation (compression, liquefication and reconversion)**"
        ):
            display_and_edit_input_data(
                api,
                data_type="reconversion_processes",
                scope=None,
                key="input_data_reconversion_processes",
                tool_version_color="blue",
            )
        with st.expander("**Secondary CO₂, electricity and heat generation**"):
            st.caption(
                read_markdown_file(
                    "md/tab_blue_input_data/description_direct_air_capture.md"
                )
            )
            display_and_edit_input_data(
                api,
                data_type="secondary_processes_blue",
                scope=None,
                key="input_data_secproc",
                tool_version_color="blue",
            )
        with st.expander("**Specific costs for materials and energy carriers**"):
            st.caption(
                read_markdown_file(
                    "md/tab_blue_input_data/description_specific_costs.md"
                ),
            )
            display_and_edit_input_data(
                api,
                data_type="specific_costs",
                scope=None,
                key="input_data_specific_costs",
                tool_version_color="blue",
            )
        with st.expander("**Conversion coefficients**"):
            st.caption(
                read_markdown_file(
                    "md/tab_blue_input_data/description_conversion_coefficients.md"
                ),
            )
            display_and_edit_input_data(
                api,
                data_type="conversion_coefficients",
                scope=None,
                key="input_data_conversion_coefficients",
                tool_version_color="blue",
            )
