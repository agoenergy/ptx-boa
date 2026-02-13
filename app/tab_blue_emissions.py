"""Content of blue emissions tab."""

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_emissions, what_is_a_boxplot
from app.plot_functions import (
    create_bar_chart_costs,
    create_box_plot,
    plot_emissions_on_map,
)
from app.ptxboa_functions import (
    aggregate_emissions,
    blue_results_over_dimension,
    get_region_list_without_subregions,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI


def content_emissions(api: PtxboaAPI):
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file("md/whatisthis_blue_emissions.md"),
            unsafe_allow_html=True,
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different source countries"
        ):
            results_per_region = blue_results_over_dimension(
                api,
                dim="region",
                parameter_list=get_region_list_without_subregions(
                    api,
                    country_name=st.session_state["country"],
                    keep=st.session_state["subregion"],
                ),
            )

        title_string = (
            f"Total greenhouse gas emissions of exporting "
            f"{st.session_state['output_product_label']} to "
            f"{st.session_state['country']}"
        )
        st.subheader(title_string)

        fig_map = plot_emissions_on_map(
            api, aggregate_emissions(results_per_region.emissions, "region")
        )
        fig_map.update_layout(
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        st.plotly_chart(fig_map, width="stretch")

        st.subheader("Emission distribution and emission components")

        st.markdown(
            (
                "These figures show the regional distribution of total greenhous gas "
                "emissions and a breakdown by category, and gas type for the "
                "selected source country."
            )
        )

        # create box plot and bar plot:
        fig1 = create_box_plot(
            aggregate_emissions(results_per_region.emissions, index="region"),
            unit=st.session_state["emissions_output_unit"],
            label="Total emissions distribution",
        )
        filtered_data = results_per_region.emissions[
            results_per_region.emissions["region"] == st.session_state["region"]
        ]

        fig2 = create_bar_chart_costs(
            pd.concat(
                [
                    aggregate_emissions(
                        filtered_data.assign(region="Total emissions"),
                        index="region",
                    ),  # here we aggregate all gas types
                    aggregate_emissions(filtered_data, index="gas_type"),
                ]
            )
        )
        doublefig = make_subplots(rows=1, cols=2, shared_yaxes=True)

        for trace in fig1.data:
            trace.showlegend = False
            doublefig.add_trace(trace, row=1, col=1)
        for trace in fig2.data:
            doublefig.add_trace(trace, row=1, col=2)

        doublefig.update_layout(barmode="stack")
        doublefig.update_layout(legend_traceorder="reversed")
        doublefig.update_yaxes(
            title_text=st.session_state["emissions_output_unit"], row=1, col=1
        )
        doublefig.update_xaxes(title_text=st.session_state["region"], row=1, col=2)
        doublefig.update_layout(
            height=350,
            margin={"l": 10, "r": 10, "t": 20, "b": 20},
        )

        # set ticklabel format:
        doublefig.update_yaxes(tickformat=",")
        doublefig.update_layout(separators=". ")

        st.plotly_chart(doublefig, width="stretch")

        what_is_a_boxplot()

        with st.container(border=True):
            help_string = " ".join(
                [
                    "This figure lets you compare total emissions and emissions by "
                    "processing step for each source country.\n\n"
                    "By default, all regions are shown, and they are sorted"
                    " by total emissions. You can change this in the filter settings."
                ]
            )
            display_emissions(
                aggregate_emissions(results_per_region.emissions, index="region"),
                (
                    aggregate_emissions(
                        results_per_region.emissions_not_modified, index="region"
                    )
                    if results_per_region.emissions_not_modified is not None
                    else None
                ),
                key="region",
                key_suffix="emissions_steps",
                titlestring="Emissions per process step for different source countries",
                help_string=help_string,
            )

        with st.container(border=True):
            help_string = " ".join(
                [
                    "This figure lets you compare total emissions and emissions by "
                    "gas type for each source country.\n\n"
                    "By default, all regions are shown, and they are sorted"
                    " by total emissions. You can change this in the filter settings."
                ]
            )
            display_emissions(
                aggregate_emissions(
                    results_per_region.emissions, index="region", columns="gas_type"
                ),
                (
                    aggregate_emissions(
                        results_per_region.emissions_not_modified,
                        index="region",
                        columns="gas_type",
                    )
                    if results_per_region.emissions_not_modified is not None
                    else None
                ),
                key="region",
                key_suffix="emissions_gases",
                titlestring="Emissions per gas type for different source countries",
                help_string=help_string,
            )

        st.divider()
        with st.expander("Detailed emissions data per region"):
            st.dataframe(results_per_region.emissions)
