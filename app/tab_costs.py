# -*- coding: utf-8 -*-
"""Content of costs tab."""
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_costs, what_is_a_boxplot
from app.plot_functions import (
    create_bar_chart_costs,
    create_box_plot,
    plot_costs_on_map,
)
from app.ptxboa_functions import move_to_tab, read_markdown_file, remove_subregions
from ptxboa.api import PtxboaAPI


def content_costs(
    api: PtxboaAPI,
    costs_per_region: pd.DataFrame,
    costs_per_scenario: pd.DataFrame,
    costs_per_res_gen: pd.DataFrame,
    costs_per_chain: pd.DataFrame,
    costs_per_region_without_user_changes: pd.DataFrame,
    costs_per_scenario_without_user_changes: pd.DataFrame,
    costs_per_res_gen_without_user_changes: pd.DataFrame,
    costs_per_chain_without_user_changes: pd.DataFrame,
):
    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_costs.md"))

    with st.container(border=True):
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

        st.plotly_chart(doublefig, use_container_width=True)

        what_is_a_boxplot()

        st.button(
            "More Info on Supply Region and Demand Country",
            on_click=move_to_tab,
            args=("Country fact sheets",),
        )

    with st.container(border=True):
        display_costs(
            remove_subregions(api, costs_per_region, st.session_state["country"]),
            (
                remove_subregions(
                    api,
                    costs_per_region_without_user_changes,
                    st.session_state["country"],
                )
                if st.session_state["user_changes_df"] is not None
                else None
            ),
            "region",
            "Costs by region",
        )

    with st.container(border=True):
        display_costs(
            costs_per_scenario,
            costs_per_scenario_without_user_changes,
            "scenario",
            "Costs by data scenario",
        )

    with st.container(border=True):
        display_costs(
            costs_per_res_gen,
            costs_per_res_gen_without_user_changes,
            "res_gen",
            "Costs by renewable electricity source",
        )

    with st.container(border=True):
        display_costs(
            costs_per_chain,
            costs_per_chain_without_user_changes,
            "chain",
            "Costs by supply chain",
            output_unit="USD/MWh",
        )
