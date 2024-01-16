# -*- coding: utf-8 -*-
"""Layout elements that get reused in several tabs."""
import pandas as pd
import streamlit as st

from app.excel_download import prepare_and_download_df_as_excel
from app.plot_functions import create_bar_chart_costs
from app.ptxboa_functions import change_index_names, config_number_columns


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
                ["With Modifications", "Without Modifications", "Difference"],
                horizontal=True,
                key=f"select_user_modificatons_data_{key}_{key_suffix}",
            )
        if select_data == "With Modifications":
            df_res = df_costs
        if select_data == "Without Modifications":
            df_res = df_costs_without_user_changes
        if select_data == "Difference":
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

    # fix index names
    change_index_names(df_res)

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
        fn = f"costs_per_{key}_{key_suffix}".strip("_")
        if st.session_state["user_changes_df"] is not None:
            fn = f"{fn}_{select_data}".lower().replace(" ", "_")
        prepare_and_download_df_as_excel(df_res, filename=fn)

    return None


def display_footer():
    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                ##### Developed by
                Öko-Institut<br/>
                Merzhauser Straße 173<br/>
                D-79100 Freiburg im Breisgau<br/>
                www.oeko.de
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                ##### On behalf of
                Agora Energiewende<br/>
                Anna-Louisa-Karsch-Str. 2<br/>
                D-10178 Berlin<br/>
                www.agora-energiewende.de
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                ##### Authors
                Christoph Heinemann<br/>
                Dr. Roman Mendelevitch<br/>
                Markus Haller<br/>
                Christian Winger<br/>
                Johannes Aschauer<br/>
                Susanne Krieger<br/>
                Katharina Göckeler<br/>
                """,
                unsafe_allow_html=True,
            )

        st.image("img/logos.png")
