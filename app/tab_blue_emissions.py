"""Content of blue emissions tab."""

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_results_bar_and_table, what_is_a_boxplot
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
    sort_by_position_in_chain,
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
                emissions_included=st.session_state["emissions_included"],
                parameter_list=get_region_list_without_subregions(
                    api, keep=st.session_state["subregion"], tool_version_color="blue"
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
        current_region_data = results_per_region.emissions[
            results_per_region.emissions["region"] == st.session_state["region"]
        ]
        current_region_data_not_modified = (
            results_per_region.emissions_not_modified[
                results_per_region.emissions_not_modified["region"]
                == st.session_state["region"]
            ]
            if results_per_region.emissions_not_modified is not None
            else None
        )

        fig2 = create_bar_chart_costs(
            pd.concat(
                [
                    aggregate_emissions(
                        current_region_data.assign(region="Total emissions"),
                        index="region",
                    ),  # here we aggregate all gas types
                    aggregate_emissions(current_region_data, index="gas_type"),
                ]
            ).sort_index()
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

        # graph with x axis: process_type, color: gas_type
        display_results_bar_and_table(
            sort_by_position_in_chain(
                aggregate_emissions(
                    current_region_data.assign(
                        gas_type=lambda x: (
                            x["gas_type"] + " (" + x["emission_type"] + ")"
                        )
                    ),
                    index="process_type",
                    columns="gas_type",
                ),
                axis="index",
            ),
            (
                sort_by_position_in_chain(
                    aggregate_emissions(
                        current_region_data_not_modified.assign(
                            gas_type=lambda x: (
                                x["gas_type"] + " (" + x["emission_type"] + ")"
                            )
                        ),
                        index="process_type",
                        columns="gas_type",
                    ),
                    axis="index",
                )
                if current_region_data_not_modified is not None
                else None
            ),
            key="scenario",
            key_suffix="gas_vs_process",
            titlestring="Emissions per gas type for different processing steps",
            help_string="",
            tool_version_color="blue",
            data_type="emissions",
            allow_sorting=False,
        )

        with st.container(border=True):
            help_string = " ".join(
                [
                    "This figure lets you compare total emissions and emissions by "
                    "processing step for each source country.\n\n"
                    "By default, all regions are shown, and they are sorted"
                    " by total emissions. You can change this in the filter settings."
                ]
            )
            display_results_bar_and_table(
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
                tool_version_color="blue",
                data_type="emissions",
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
            display_results_bar_and_table(
                aggregate_emissions(
                    results_per_region.emissions.assign(
                        gas_type=lambda x: (
                            x["gas_type"] + " (" + x["emission_type"] + ")"
                        )
                    ),
                    index="region",
                    columns="gas_type",
                ),
                (
                    aggregate_emissions(
                        results_per_region.emissions_not_modified.assign(
                            gas_type=lambda x: (
                                x["gas_type"] + " (" + x["emission_type"] + ")"
                            )
                        ),
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
                tool_version_color="blue",
                data_type="emissions",
            )

    blue_chains = api.get_dimension("chain", "blue")
    blue_chain_labels = blue_chains["chain_name"].to_dict()

    with st.container(border=True):
        with st.spinner("Please wait. Calculating results for conversion locations."):
            results_supply_demand = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=pd.Series(
                    [
                        st.session_state["chain"].replace(
                            "__prod_in_demand", "__prod_in_supply"
                        ),
                        st.session_state["chain"].replace(
                            "__prod_in_supply", "__prod_in_demand"
                        ),
                    ]
                ),
            )

        help_string = " ".join(
            [
                "This figure lets you compare total emissions and emissions by",
                "processing step conversion location in supply or demand country",
            ]
        )

        display_results_bar_and_table(
            aggregate_emissions(
                results_supply_demand.emissions, index="chain", columns="process_type"
            ),
            (
                aggregate_emissions(
                    results_supply_demand.emissions_not_modified,
                    index="chain",
                    columns="process_type",
                )
                if results_supply_demand.emissions_not_modified is not None
                else None
            ),
            key="chain",
            key_suffix="demand_supply",
            titlestring="Emissions for converting in supply or demand country",
            help_string=help_string,
            x_label_mapping={
                k: (
                    f"{v}<br>conversion in "
                    f"{'supply' if 'prod_in_supply' in k else 'demand'} country"
                )
                for k, v in blue_chain_labels.items()
            },
            tool_version_color="blue",
            data_type="emissions",
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different supply chains of output "
            "product."
        ):
            equal_output_product_chains = blue_chains.loc[
                blue_chains.index.str.endswith(
                    f"prod_in_{st.session_state['conversion_location']}"
                )
                & (blue_chains["FLOW_OUT"] == st.session_state["output_product"])
            ].index

            results_equal_output_product = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=equal_output_product_chains,
            )

        help_string = " ".join(
            [
                "This figure lets you comparetotal emissions and emissions by",
                "processiong step",
                "for different technology chains that produce ",
                f"{st.session_state['output_product_label']}.",
            ]
        )

        display_results_bar_and_table(
            aggregate_emissions(
                results_equal_output_product.emissions,
                index="chain",
                columns="process_type",
            ),
            (
                aggregate_emissions(
                    results_equal_output_product.emissions_not_modified,
                    index="chain",
                    columns="process_type",
                )
                if results_equal_output_product.emissions_not_modified is not None
                else None
            ),
            key="chain",
            key_suffix="equal_product",
            titlestring="Emissions for different technology chains",
            help_string=help_string,
            x_label_mapping=blue_chain_labels,
            tool_version_color="blue",
            data_type="emissions",
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different output products."
        ):
            if st.session_state["reformer"] is not None:
                equal_reformer_chains = blue_chains.loc[
                    blue_chains.index.str.endswith(
                        f"prod_in_{st.session_state['conversion_location']}"
                    )
                    & (
                        (blue_chains["ELY"] == st.session_state["reformer"])
                        | (blue_chains["ELY_I"] == st.session_state["reformer"])
                    )
                ].index
            else:
                equal_reformer_chains = blue_chains.loc[
                    blue_chains.index.str.endswith(
                        f"prod_in_{st.session_state['conversion_location']}"
                    )
                    & ((blue_chains["ELY"] == "") & (blue_chains["ELY_I"] == ""))
                ].index

            results_equal_routes = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=equal_reformer_chains,
                override_session_state={
                    "output_unit": "USD/MWh"
                },  # api always wants cost unit
            )

        help_string = " ".join(
            [
                "This figure lets you compare total emissions and emissions by",
                "processiong step",
                "for different products with comparable technology chains.",
            ]
        )

        display_results_bar_and_table(
            aggregate_emissions(
                results_equal_routes.emissions, index="chain", columns="process_type"
            ),
            (
                aggregate_emissions(
                    results_equal_routes.emissions_not_modified,
                    index="chain",
                    columns="process_type",
                )
                if results_equal_routes.emissions_not_modified is not None
                else None
            ),
            key="chain",
            key_suffix="equal_reformer",
            titlestring="Emissions for different products",
            output_unit=st.session_state["emissions_output_unit"].replace("/t", "/MWh"),
            help_string=help_string,
            x_label_mapping=blue_chain_labels,
            tool_version_color="blue",
            data_type="emissions",
        )

        st.divider()
        with st.expander("Detailed emissions data per region"):
            st.warning("Will be removed in final version.")
            st.dataframe(results_per_region.emissions)
