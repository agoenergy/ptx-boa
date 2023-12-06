# -*- coding: utf-8 -*-
"""Content of dashboard tab."""
import pandas as pd
import streamlit as st
from plotly.subplots import make_subplots

from app.layout_elements import display_costs
from app.plot_functions import (
    create_bar_chart_costs,
    create_box_plot,
    plot_costs_on_map,
)
from app.ptxboa_functions import move_to_tab, remove_subregions
from ptxboa.api import PtxboaAPI


def content_dashboard(
    api: PtxboaAPI,
    costs_per_region: pd.DataFrame,
    costs_per_scenario: pd.DataFrame,
    costs_per_res_gen: pd.DataFrame,
    costs_per_chain: pd.DataFrame,
):
    with st.expander("What is this?"):
        st.markdown(
            """
This is the dashboard. It shows key results according to your settings:
- a map and a box plot that show the spread and the
regional distribution of total costs across supply regions
- a split-up of costs by category for your chosen supply region
- key information on your chosen demand country.
- total cost and cost components for different supply countries, scenarios,
renewable electricity sources and process chains.

Switch to other tabs to explore data and results in more detail!
            """
        )

    c_1, c_2 = st.columns([2, 1])

    with c_1:
        fig_map = plot_costs_on_map(
            api, costs_per_region, scope="world", cost_component="Total"
        )
        st.plotly_chart(fig_map, use_container_width=True)

    with c_2:
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
        doublefig.update_layout(title_text="Cost distribution and details:")
        st.plotly_chart(doublefig, use_container_width=True)

    st.button(
        "More Info on Supply Region and Demand Country",
        on_click=move_to_tab,
        args=("Country fact sheets",),
    )

    display_costs(
        remove_subregions(api, costs_per_region, st.session_state["country"]),
        "region",
        "Costs by region:",
    )

    display_costs(costs_per_scenario, "scenario", "Costs by data scenario:")

    display_costs(
        costs_per_res_gen, "res_gen", "Costs by renewable electricity source:"
    )

    display_costs(
        costs_per_chain, "chain", "Costs by supply chain:", output_unit="USD/MWh"
    )
