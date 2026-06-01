"""Content of blue emissions tab."""

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_results_bar_and_table, what_is_a_boxplot
from app.plot_functions import (
    create_bar_chart_results,
    create_box_plot,
    plot_emissions_on_map,
)
from app.ptxboa_functions import (
    aggregate_emissions,
    blue_results_over_dimension,
    check_if_input_is_needed,
    filter_blue_supply_regions,
    read_markdown_file,
    sort_by_position_in_chain,
)
from ptxboa.api import PtxboaAPI


def content_emissions(api: PtxboaAPI):
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file("md/tab_blue_emissions/whatisthis_blue_emissions.md"),
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
                parameter_list=pd.Series(
                    filter_blue_supply_regions(api, st.session_state["country"])
                ),
            )

        title_string = (
            f"Total greenhouse gas emissions of exporting "
            f"{st.session_state['output_product_label']} to "
            f"{st.session_state['country']}"
        )
        st.subheader(title_string)
        st.markdown(
            read_markdown_file("md/tab_blue_emissions/description_emission_map.md")
        )

        fig_map = plot_emissions_on_map(
            api, aggregate_emissions(results_per_region.emissions, "region")
        )
        fig_map.update_layout(
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        st.plotly_chart(fig_map, width="stretch")

        st.subheader(
            read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_distribution.md"
            )
        )
        st.markdown(
            read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_distribution.md"
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

        fig2 = create_bar_chart_results(
            pd.concat(
                [
                    aggregate_emissions(
                        current_region_data.assign(region="Total emissions"),
                        index="region",
                    ),  # here we aggregate all gas types
                    aggregate_emissions(current_region_data, index="gas_type"),
                ]
            ).sort_index(),
            float_format=".2f",
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

        blue_chains = api.get_dimension("chain", "blue")
        blue_chain_labels = blue_chains["chain_name"].to_dict()

    if st.session_state["region"] != st.session_state["country"]:
        with st.container(border=True):
            conversion_location_title = read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_per_conversion_location.md"
            )
            conversion_location_help = read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_per_conversion_location.md"  # noqa E501
            )
            if st.session_state["chain"].endswith("__transport_NH3-L"):
                st.subheader(conversion_location_title)
                st.markdown(conversion_location_help)
                chain_label = blue_chain_labels.get(
                    st.session_state["chain"], st.session_state["chain"]
                )
                st.warning(
                    f'For the conversion route "{chain_label}", '
                    "conversion can only take place in the supply country."
                )
            else:
                with st.spinner(
                    "Please wait. Calculating results for conversion locations."
                ):
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

                supply = st.session_state["region"]
                demand = st.session_state["country"]
                xlabel_mapping = {
                    k: (
                        f"{v}<br>conversion in "
                        f"{supply if 'prod_in_supply' in k else demand}"
                    )
                    for k, v in blue_chain_labels.items()
                }

                display_results_bar_and_table(
                    aggregate_emissions(
                        results_supply_demand.emissions,
                        index="chain",
                        columns="process_type",
                    ).sort_index(ascending=False),
                    (
                        aggregate_emissions(
                            results_supply_demand.emissions_not_modified,
                            index="chain",
                            columns="process_type",
                        ).sort_index(ascending=False)
                        if results_supply_demand.emissions_not_modified is not None
                        else None
                    ),
                    key="chain",
                    key_suffix="demand_supply",
                    titlestring=conversion_location_title,
                    help_string=conversion_location_help,
                    x_label_mapping=xlabel_mapping,
                    xaxis_title="Conversion location",
                    tool_version_color="blue",
                    data_type="emissions",
                    sorting="off",
                )

    with st.container(border=True):
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
            titlestring=read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_per_processing_step.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_per_processing_step.md"  # noqa E501
            ),
            tool_version_color="blue",
            data_type="emissions",
            sorting="off",
        )

    with st.container(border=True):
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
            titlestring=read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_per_region_color_step.md"  # noqa E501
            ),
            help_string=read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_per_region_color_step.md"  # noqa E501
            ),
            tool_version_color="blue",
            data_type="emissions",
        )

    with st.container(border=True):
        display_results_bar_and_table(
            aggregate_emissions(
                results_per_region.emissions.assign(
                    gas_type=lambda x: x["gas_type"] + " (" + x["emission_type"] + ")"
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
            titlestring=read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_per_region_color_gas.md"  # noqa E501
            ),
            help_string=read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_per_region_color_gas.md"  # noqa E501
            ),
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
                & (blue_chains["flow_out"] == st.session_state["output_product"])
            ].index

            results_equal_output_product = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=equal_output_product_chains,
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
            titlestring=read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_equal_product.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_equal_product.md"
            )
            + f" {st.session_state['output_product_label']}.",
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
                    & blue_chains["flow_out"].isin(
                        st.session_state["output_product_group"]
                    )
                ].index
            else:
                equal_reformer_chains = blue_chains.loc[
                    blue_chains.index.str.endswith(
                        f"prod_in_{st.session_state['conversion_location']}"
                    )
                    & ((blue_chains["ELY"] == "") & (blue_chains["ELY_I"] == ""))
                    & blue_chains["flow_out"].isin(
                        st.session_state["output_product_group"]
                    )
                ].index

            results_equal_routes = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=equal_reformer_chains,
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
            titlestring=read_markdown_file(
                "md/tab_blue_emissions/figure_title_emission_equal_reformer.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_emissions/figure_description_emission_equal_reformer.md"
            ),
            output_unit=st.session_state["emissions_output_unit"].replace("/t", "/MWh"),
            x_label_mapping=blue_chain_labels,
            tool_version_color="blue",
            data_type="emissions",
        )

    needs_secondary_co2 = check_if_input_is_needed(
        api,
        flow_code="CO2-G",
        chain=st.session_state["chain"],
        scenario=st.session_state["scenario"],
        tool_version_color="blue",
    )

    with st.container(border=True):
        secproc_co2_title = read_markdown_file(
            "md/tab_blue_emissions/figure_title_emission_per_secproc_co2.md"
        )
        secproc_co2_help = read_markdown_file(
            "md/tab_blue_emissions/figure_description_emission_per_secproc_co2.md"
        )
        if needs_secondary_co2:
            with st.spinner(
                "Please wait. Calculating results for different secondary CO₂ sources."
            ):
                results_per_secproc_co2 = blue_results_over_dimension(
                    api,
                    dim="secproc_co2",
                    emissions_included=st.session_state["emissions_included"],
                    parameter_list=pd.Series(
                        [
                            "CO2 from other industrial sources",
                            "CO2 from hard-to-abate or sustainable sources",
                            "Direct Air Capture (blue)",
                        ]
                    ),
                )

            display_results_bar_and_table(
                df=aggregate_emissions(
                    results_per_secproc_co2.emissions,
                    index="secproc_co2",
                    columns="process_type",
                ),
                df_without_user_changes=(
                    aggregate_emissions(
                        results_per_secproc_co2.emissions_not_modified,
                        index="secproc_co2",
                        columns="process_type",
                    )
                    if results_per_secproc_co2.emissions_not_modified is not None
                    else None
                ),
                key="secproc_co2",
                titlestring=secproc_co2_title,
                help_string=secproc_co2_help,
                tool_version_color="blue",
                data_type="emissions",
                x_label_mapping={
                    "Direct Air Capture (blue)": "Direct Air Capture",
                    "CO2 from other industrial sources": "CO₂ from other industrial sources",  # noqa: E501
                    "CO2 from hard-to-abate or sustainable sources": "CO₂ from hard-to-abate or sustainable sources",  # noqa: E501
                },
                xaxis_title="Secondary CO₂ source",
                sorting="off",
            )
        else:
            st.subheader(secproc_co2_title)
            st.markdown(secproc_co2_help)
            chain_label = blue_chain_labels.get(
                st.session_state["chain"], st.session_state["chain"]
            )
            st.warning(f"{chain_label} does not need secondary CO₂")
