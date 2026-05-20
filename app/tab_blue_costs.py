"""Content of costs tab."""

import logging

import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_results_bar_and_table, what_is_a_boxplot
from app.plot_functions import (
    create_bar_chart_results,
    create_box_plot,
    plot_costs_on_map,
)
from app.ptxboa_functions import (
    blue_results_over_dimension,
    filter_blue_supply_regions,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI

logger = logging.getLogger()


def content_costs(api: PtxboaAPI):
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file("md/tab_blue_costs/whatisthis_blue_costs.md"),
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
                    filter_blue_supply_regions(api, st.session_state["region"])
                ),
            )

        title_string = (
            f"Cost of exporting "
            f"{st.session_state['output_product_label']} to "
            f"{st.session_state['country']} "
            f"in {st.session_state['scenario'].split(' ')[0]}"  # data year
        )
        st.subheader(title_string)

        st.markdown(read_markdown_file("md/tab_blue_costs/description_cost_map.md"))

        fig_map = plot_costs_on_map(
            api, results_per_region.costs, scope="world", cost_component="Total"
        )
        fig_map.update_layout(
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        st.plotly_chart(fig_map, width="stretch")

        st.subheader(
            read_markdown_file("md/tab_blue_costs/figure_title_cost_distribution.md")
        )
        st.markdown(
            read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_distribution.md"
            )
        )

        # create box plot and bar plot:
        fig1 = create_box_plot(
            results_per_region.costs, unit=st.session_state["output_unit"]
        )
        filtered_data = results_per_region.costs[
            results_per_region.costs.index == st.session_state["region"]
        ]
        fig2 = create_bar_chart_results(filtered_data)
        doublefig = make_subplots(rows=1, cols=2, shared_yaxes=True)

        for trace in fig1.data:
            trace.showlegend = False
            doublefig.add_trace(trace, row=1, col=1)
        for trace in fig2.data:
            doublefig.add_trace(trace, row=1, col=2)

        doublefig.update_layout(barmode="stack")
        doublefig.update_layout(legend_traceorder="reversed")
        doublefig.update_yaxes(title_text=st.session_state["output_unit"], row=1, col=1)
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

    with st.container(border=True):
        conversion_location_title = read_markdown_file(
            "md/tab_blue_costs/figure_title_cost_per_conversion_location.md"
        )
        conversion_location_help = read_markdown_file(
            "md/tab_blue_costs/figure_description_cost_per_conversion_location.md"
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
                results_supply_demand.costs.sort_index(ascending=False),
                (
                    results_supply_demand.costs_not_modified.sort_index(ascending=False)
                    if results_supply_demand.costs_not_modified is not None
                    else None
                ),
                key="chain",
                key_suffix="demand_supply",
                titlestring=conversion_location_title,
                help_string=conversion_location_help,
                x_label_mapping=xlabel_mapping,
                xaxis_title="Conversion location",
                tool_version_color="blue",
                sorting="off",
            )

    with st.container(border=True):
        display_results_bar_and_table(
            results_per_region.costs,
            results_per_region.costs_not_modified,
            "region",
            titlestring=read_markdown_file(
                "md/tab_blue_costs/figure_title_cost_per_region.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_per_region.md"
            ),
            tool_version_color="blue",
        )

    with st.container(border=True):
        with st.spinner("Please wait. Calculating results for different WACC values."):
            results_per_wacc = blue_results_over_dimension(
                api,
                dim="WACC",
                emissions_included=st.session_state["emissions_included"],
            )

        conversion_region = (
            st.session_state["region"]
            if st.session_state["conversion_location"] == "supply"
            else st.session_state["country"]
        )
        display_results_bar_and_table(
            results_per_wacc.costs,
            results_per_wacc.costs_not_modified,
            key="scenario",
            key_suffix="sensitivity_wacc",
            titlestring=f"Costs for different WACC values in {conversion_region}",
            help_string=read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_per_WACC.md"
            ),
            tool_version_color="blue",
            sorting="ascending",
            allow_diff_view=False,
            xaxis_title="WACC (%)",
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different natural gas prices."
        ):
            results_per_ng_price = blue_results_over_dimension(
                api,
                dim="Natural gas price",
                emissions_included=st.session_state["emissions_included"],
            )

        display_results_bar_and_table(
            results_per_ng_price.costs,
            results_per_ng_price.costs_not_modified,
            key="scenario",
            key_suffix="sensitivity_ng_price",
            titlestring=(
                "Costs for different natural gas prices "
                f"in {st.session_state['region']}"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_per_natural_gas_price.md"
            ),
            tool_version_color="blue",
            sorting="ascending",
            allow_diff_view=False,
            xaxis_title="Natural gas price (USD/kWh)",
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
            results_equal_output_product.costs,
            results_equal_output_product.costs_not_modified,
            key="chain",
            key_suffix="equal_product",
            titlestring=read_markdown_file(
                "md/tab_blue_costs/figure_title_cost_equal_product.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_equal_product.md"
            )
            + f" {st.session_state['output_product_label']}.",
            x_label_mapping=blue_chain_labels,
            tool_version_color="blue",
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

            if len(equal_reformer_chains) == 0:
                logger.warning(
                    "No equal_reformer_chains for reformer "
                    f"'{st.session_state['reformer']}'"
                )

            results_equal_routes = blue_results_over_dimension(
                api,
                dim="chain",
                emissions_included=st.session_state["emissions_included"],
                parameter_list=equal_reformer_chains,
            )

        display_results_bar_and_table(
            results_equal_routes.costs,
            results_equal_routes.costs_not_modified,
            key="chain",
            key_suffix="equal_reformer",
            titlestring=read_markdown_file(
                "md/tab_blue_costs/figure_title_cost_equal_reformer.md"
            ),
            help_string=read_markdown_file(
                "md/tab_blue_costs/figure_description_cost_equal_reformer.md"
            ),
            output_unit="USD/MWh",
            x_label_mapping=blue_chain_labels,
            tool_version_color="blue",
        )
