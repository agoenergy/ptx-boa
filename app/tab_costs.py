# -*- coding: utf-8 -*-
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
    costs_over_dimension,
    get_region_list_without_subregions,
    move_to_tab,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI


def content_costs(api: PtxboaAPI):
    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_costs.md"))

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different source regions"
        ):
            costs_per_region, costs_per_region_without_user_changes = (
                costs_over_dimension(
                    api,
                    dim="region",
                    parameter_list=get_region_list_without_subregions(
                        api,
                        country_name=st.session_state["country"],
                        keep=st.session_state["subregion"],
                    ),
                )
            )

        title_string = (
            f"Cost of exporting "
            f"{st.session_state['chain']} to "
            f"{st.session_state['country']}"
        )
        st.subheader(title_string)

        fig_map = plot_costs_on_map(
            api, costs_per_region, scope="world", cost_component="Total"
        )
        fig_map.update_layout(
            margin={"l": 10, "r": 10, "t": 10, "b": 10},
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.subheader("Cost distribution and cost components")
        # create box plot and bar plot:
        fig1 = create_box_plot(costs_per_region)
        filtered_data = costs_per_region[
            costs_per_region.index == st.session_state["region"]
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
        doublefig.update_layout(separators="* .*")

        st.plotly_chart(doublefig, use_container_width=True)

        what_is_a_boxplot()

        st.button(
            "More Info on Supply Region and Demand Country",
            on_click=move_to_tab,
            args=("Country fact sheets",),
        )

    with st.container(border=True):
        display_costs(
            costs_per_region,
            costs_per_region_without_user_changes,
            "region",
            "Costs by region",
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different data scenarios."
        ):
            costs_per_scenario, costs_per_scenario_without_user_changes = (
                costs_over_dimension(
                    api,
                    dim="scenario",
                )
            )
        display_costs(
            costs_per_scenario,
            costs_per_scenario_without_user_changes,
            "scenario",
            "Costs by data scenario",
        )

    with st.container(border=True):
        with st.spinner(
            (
                "Please wait. Calculating results for different renewable electricity "
                "sources."
            )
        ):
            costs_per_res_gen, costs_per_res_gen_without_user_changes = (
                costs_over_dimension(
                    api,
                    dim="res_gen",
                    # TODO: here we remove PV tracking manually, fix in data
                    parameter_list=[
                        x
                        for x in api.get_dimension("res_gen").index.to_list()
                        if x != "PV tracking"
                    ],
                )
            )
        display_costs(
            costs_per_res_gen,
            costs_per_res_gen_without_user_changes,
            "res_gen",
            "Costs by renewable electricity source",
        )

    with st.container(border=True):
        with st.spinner(
            "Please wait. Calculating results for different supply chains."
        ):
            costs_per_chain, costs_per_chain_without_user_changes = (
                costs_over_dimension(
                    api,
                    dim="chain",
                    override_session_state={"output_unit": "USD/MWh"},
                )
            )
        display_costs(
            costs_per_chain,
            costs_per_chain_without_user_changes,
            "chain",
            "Costs by supply chain",
            output_unit="USD/MWh",
            default_select=1,
            default_manual_select=[
                x
                for x in costs_per_chain.index
                if st.session_state["electrolyzer"] in x
            ],
        )
