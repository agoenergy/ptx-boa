# -*- coding: utf-8 -*-
"""Layout elements that get reused in several tabs."""
import pandas as pd
import streamlit as st

from app.plot_functions import create_bar_chart_costs
from app.ptxboa_functions import config_number_columns


def display_costs(
    df_costs: pd.DataFrame,
    df_costs_without_user_changes: pd.DataFrame,
    key: str,
    titlestring: str,
    key_suffix: str = "",
    output_unit: str | None = None,
):
    """Display costs as table and bar chart."""
    if output_unit is None:
        output_unit = st.session_state["output_unit"]
    key_suffix = key_suffix.lower().replace(" ", "_")
    st.subheader(titlestring)

    c1, c2 = st.columns(2)

    # select which dataset to display:
    if st.session_state["user_changes_df"] is not None:
        with c2:
            st.info("Input data has been modified. Select which data to display.")
            select_data = st.radio(
                "Select data to display",
                ["with user modifications", "without user modifications", "difference"],
                horizontal=True,
                key=f"select_data_{key}_{key_suffix}",
            )
        if select_data == "with user modifications":
            df_res = df_costs
        if select_data == "without user modifications":
            df_res = df_costs_without_user_changes
        if select_data == "difference":
            df_res = df_costs - df_costs_without_user_changes
    else:
        df_res = df_costs.copy()

    with c1:
        # select filter:
        show_which_data = st.radio(
            "Select elements to display:",
            ["All", "Manual select"],
            index=0,
            horizontal=True,
            key=f"show_which_data_{key}_{key_suffix}",
        )

        # apply filter:
        if show_which_data == "Manual select":
            ind_select = st.multiselect(
                "Select regions:",
                df_res.index.values,
                default=df_res.index.values,
                key=f"select_data_{key}_{key_suffix}",
            )
            df_res = df_res.loc[ind_select]

        # sort:
        sort_ascending = st.toggle(
            "Sort by total costs?",
            value=True,
            key=f"sort_data_{key}_{key_suffix}",
        )
        if sort_ascending:
            df_res = df_res.sort_values(["Total"], ascending=True)
    # create graph:
    fig = create_bar_chart_costs(
        df_res,
        current_selection=st.session_state[key],
        output_unit=output_unit,
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("**Data**"):
        column_config = config_number_columns(df_res, format=f"%.1f {output_unit}")
        st.dataframe(df_res, use_container_width=True, column_config=column_config)
    return None
