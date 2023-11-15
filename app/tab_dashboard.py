# -*- coding: utf-8 -*-
"""Content of dashboard tab."""
import streamlit as st
from plotly.subplots import make_subplots

from app.ptxboa_functions import (
    create_bar_chart_costs,
    create_box_plot,
    create_world_map,
)


def _create_infobox(context_data: dict):
    data = context_data["infobox"]
    st.markdown(f"**Key information on {st.session_state['country']}:**")
    demand = data.at[st.session_state["country"], "Projected H2 demand [2030]"]
    info1 = data.at[st.session_state["country"], "key_info_1"]
    info2 = data.at[st.session_state["country"], "key_info_2"]
    info3 = data.at[st.session_state["country"], "key_info_3"]
    info4 = data.at[st.session_state["country"], "key_info_4"]
    st.markdown(f"* Projected H2 demand in 2030: {demand}")

    def write_info(info):
        if isinstance(info, str):
            st.markdown(f"* {info}")

    write_info(info1)
    write_info(info2)
    write_info(info3)
    write_info(info4)


def content_dashboard(api, res_costs: dict, context_data: dict):
    with st.expander("What is this?"):
        st.markdown(
            """
This is the dashboard. It shows key results according to your settings:
- a map and a box plot that show the spread and the
regional distribution of total costs across supply regions
- a split-up of costs by category for your chosen supply region
- key information on your chosen demand country.

Switch to other tabs to explore data and results in more detail!
            """
        )

    c_1, c_2 = st.columns([2, 1])

    with c_1:
        create_world_map(api, res_costs)

    with c_2:
        # create box plot and bar plot:
        fig1 = create_box_plot(res_costs)
        filtered_data = res_costs[res_costs.index == st.session_state["region"]]
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

        _create_infobox(context_data)
