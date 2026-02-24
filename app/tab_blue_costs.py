"""Content of costs tab."""

import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_costs, what_is_a_boxplot
from app.plot_functions import (
    create_bar_chart_costs,
    create_box_plot,
    plot_costs_on_map,
)
from app.ptxboa_functions import (
    blue_results_over_dimension,
    get_region_list_without_subregions,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI


def content_costs(api: PtxboaAPI):
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file("md/whatisthis_blue_costs.md"), unsafe_allow_html=True
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different source countries"
        ):
            results_per_region = blue_results_over_dimension(
                api,
                dim="region",
                parameter_list=get_region_list_without_subregions(
                    api, keep=st.session_state["subregion"], tool_version_color="blue"
                ),
            )

        title_string = (
            f"Cost of exporting "
            f"{st.session_state['output_product_label']} to "
            f"{st.session_state['country']}"
        )
        st.subheader(title_string)

        st.markdown(
            (
                "This map shows delivered costs for the selected product and demand"
                " country, for different source countries. Move your mouse over a "
                "marker for additional information."
            )
        )

        fig_map = plot_costs_on_map(
            api, results_per_region.costs, scope="world", cost_component="Total"
        )
        fig_map.update_layout(
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        st.plotly_chart(fig_map, width="stretch")

        st.subheader("Cost distribution and cost components")

        st.markdown(
            (
                "These figures show the regional distribution of costs"
                " and a breakdown by category for the selected source country."
            )
        )

        # create box plot and bar plot:
        fig1 = create_box_plot(
            results_per_region.costs, unit=st.session_state["output_unit"]
        )
        filtered_data = results_per_region.costs[
            results_per_region.costs.index == st.session_state["region"]
        ]
        fig2 = create_bar_chart_costs(filtered_data)
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

    with st.container(border=True):
        help_string = " ".join(
            [
                "This figure lets you compare total costs and cost components by source"
                " country.\n\n By default, all regions are shown, and they are sorted"
                " by total costs. You can change this in the filter settings."
            ]
        )
        display_costs(
            results_per_region.costs,
            results_per_region.costs_not_modified,
            "region",
            "Costs for different source countries",
            help_string=help_string,
        )

    with st.container(border=True):
        with st.spinner("Please wait. Calculating results for different WACC values."):
            results_per_wacc = blue_results_over_dimension(api, dim="WACC")

        help_string = " ".join(
            [
                "This figure lets you compare total costs and cost components "
                "by WACC in the supply country. "
                "The value from input data is altered by +-10%."
            ]
        )
        display_costs(
            results_per_wacc.costs,
            results_per_wacc.costs_not_modified,
            "scenario",
            "Costs for different WACC values in the supply country",
            help_string=help_string,
        )

    blue_chains = api.get_dimension("chain", "blue")
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
                parameter_list=equal_output_product_chains,
                override_session_state={"output_unit": "USD/MWh"},
            )

        help_string = " ".join(
            [
                "This figure lets you compare total costs and cost components"
                " for different technology chains that produce "
                f"{st.session_state['output_product_label']}."
            ]
        )

        display_costs(
            results_equal_output_product.costs,
            results_equal_output_product.costs_not_modified,
            key="chain",
            key_suffix="equal_product",
            titlestring="Costs for different technology chains",
            output_unit="USD/MWh",
            help_string=help_string,
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
                parameter_list=equal_reformer_chains,
                override_session_state={"output_unit": "USD/MWh"},
            )

        help_string = " ".join(
            [
                "This figure lets you compare total costs and cost components"
                " for different products with comparable technology chains."
            ]
        )

        display_costs(
            results_equal_routes.costs,
            results_equal_routes.costs_not_modified,
            key="chain",
            key_suffix="equal_reformer",
            titlestring="Costs for different products",
            output_unit="USD/MWh",
            help_string=help_string,
        )
