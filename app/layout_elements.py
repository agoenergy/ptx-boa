# -*- coding: utf-8 -*-
"""Layout elements that get reused in several tabs."""
from typing import Literal

import pandas as pd
import streamlit as st

from app.excel_download import prepare_and_download_df_as_excel
from app.plot_functions import create_bar_chart_costs
from app.ptxboa_functions import (
    change_index_names,
    config_number_columns,
    get_column_config,
    get_data_type_from_input_data,
    read_markdown_file,
)
from app.user_data import register_user_changes
from ptxboa.api import PtxboaAPI


def display_costs(
    df_costs: pd.DataFrame,
    df_costs_without_user_changes: pd.DataFrame,
    key: str,
    titlestring: str,
    key_suffix: str = "",
    output_unit: str | None = None,
    default_select: int = 0,
    default_manual_select: str | None = None,
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
                "Data to display",
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

    if default_manual_select is None:
        default_manual_select = df_res.index.values

    with c1:
        if len(df_res) > 13:
            select_options = [
                "All",
                "Manual selection",
                "Cheapest 10",
            ]
        else:
            select_options = ["All", "Manual selection"]
        # select filter:
        show_which_data = st.radio(
            "Elements to display:",
            select_options,
            index=default_select,
            horizontal=True,
            key=f"show_which_data_{key}_{key_suffix}",
        )

        # apply filter:
        if show_which_data == "Manual selection":
            ind_select = st.multiselect(
                "Select elements:",
                df_res.index.values,
                default=default_manual_select,
                key=f"select_data_{key}_{key_suffix}",
                label_visibility="collapsed",
            )
            df_res = df_res.loc[ind_select]

        if show_which_data == "Cheapest 10":
            ind_select = (
                df_res.sort_values(["Total"], ascending=True).iloc[:10].index.to_list()
            )
            # append the setting from the sidebar if not in cheapest 10
            if (
                st.session_state[key] not in ind_select
                and st.session_state[key] in df_res.index
            ):
                ind_select.append(st.session_state[key])
            df_res = df_res.loc[ind_select]
            sort_ascending = False

        else:
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

    # add explainer for costs by supply chain comparison:
    if titlestring == "Costs by supply chain":
        if st.session_state["output_unit"] == "USD/t":
            unit_note = (
                "The output unit is set to USD/MWh in order to compare energy carriers"
                " with different densities. "
            )
        else:
            unit_note = ""
        st.caption(
            (
                f"**Note**: {unit_note}Green Iron is not shown in this comparison "
                "as it is not an energy carrier."
            )
        )

    with st.expander("**Data**"):
        column_config = config_number_columns(df_res, format=f"%.1f {output_unit}")
        st.dataframe(df_res, use_container_width=True, column_config=column_config)
        fn = f"costs_per_{key}_{key_suffix}".strip("_")
        if st.session_state["user_changes_df"] is not None:
            fn = f"{fn}_{select_data}".lower().replace(" ", "_")
        prepare_and_download_df_as_excel(df_res, filename=fn)

    return None


@st.cache_resource()
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
                www.agora-industry.org<br/>
                www.agora-energiewende.org
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

        # TODO: fix uneven height and vertical alignment of logos
        c1, c2, c3, c4 = st.columns(4, gap="medium")
        with c1:
            st.image("img/oeko_logo_612x306.png")
        with c2:
            st.image("img/agora-energiewende_logo_612x306.png")
        with c3:
            st.image("img/Agora_Industry_logo_612x306.png")
        with c4:
            st.image("img/PtX-Hub_Logo_international_612x306.png")


def _form_data_editor(
    key,
    df,
    df_orig,
    index,
    columns,
    missing_index_name,
    missing_index_value,
    column_config,
):
    if f"{key}_number" not in st.session_state:
        st.session_state[f"{key}_number"] = 0
    editor_key = f"{key}_{st.session_state[f'{key}_number']}"

    with st.form(key=f"{key}_form", border=False):
        st.info(
            (
                "You can edit data directly in the table. When done, click the "
                "**Apply changes** button below to rerun calculations."
            )
        )

        st.form_submit_button(
            "Apply changes",
            type="primary",
            on_click=register_user_changes,
            kwargs={
                "missing_index_name": missing_index_name,
                "missing_index_value": missing_index_value,
                "index": index,
                "columns": columns,
                "values": "value",
                "df_tab": df,
                "df_orig": df_orig,
                "key": key,
                "editor_key": editor_key,
            },
        )

        df = st.data_editor(
            df,
            use_container_width=True,
            key=editor_key,
            num_rows="fixed",
            disabled=[index],
            column_config=column_config,
        )

    return df


def display_and_edit_input_data(
    api: PtxboaAPI,
    data_type: Literal[
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes",
        "CAPEX",
        "full load hours",
        "WACC",
        "specific_costs",
        "conversion_coefficients",
        "dac_and_desalination",
        "storage",
    ],
    scope: Literal["world", "Argentina", "Morocco", "South Africa"],
    key: str,
) -> pd.DataFrame:
    """
    Display a subset of the input data.

    Data is displayed either as static dataframe or inside a st.form
    based on session state variable `edit_input_data`.

    Parameters
    ----------
    api : PtxboaAPI
        an instance of the api class
    data_type : str
        the data type which should be selected. Needs to be one of
        "electricity_generation", "conversion_processes", "transportation_processes",
        "reconversion_processes", "CAPEX", "full load hours", "WACC",
        "specific costs", "conversion_coefficients" and "dac_and_desalination"
    scope : Literal[None, "world", "Argentina", "Morocco", "South Africa"]
        The regional scope. Is automatically set to None for data of
        data type "conversion_processes" and "transportation_processes" which is not
        region specific.
    key : str
        A key for the data editing layout element. Needs to be unique in the app.
        Several session state variables are derived from this key::

            - st.session_state[f"{key}_number"]:
                This is initialized with 0 and incremented by 1 whenever any input
                value got rejected by the callback function
                :func:`register_user_changes`. This will trigger a re-rendering of the
                data_editor widget and thus reset modifications on empty values.
            - st.session_state[f"{key}_form"]:
                the key for the form the editor lives in
            - st_session_state[f"{key}_{st.session_state[f'{key}_number']}"]:
                the name of this session state variable consists of the `key` and the
                current `{key}_number`. It refers to the st.data_editor widget.
                Whenever the key_number changes, the editor widget gets a new key and
                is initialized from scratch.

    Returns
    -------
    pd.DataFrame
    """
    df = get_data_type_from_input_data(api, data_type=data_type, scope=scope)
    df_orig = df.copy()

    if data_type in [
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes",
        "dac_and_desalination",
        "storage",
    ]:
        index = "process_code"
        columns = "parameter_code"
        missing_index_name = "source_region_code"
        missing_index_value = None
        column_config = get_column_config()

    if data_type == "conversion_processes":
        custom_column_config = {
            "CAPEX": st.column_config.NumberColumn(
                format="%.0f USD/[unit]",
                min_value=0,
                help=(
                    "unit is [t] for Green iron reduction and [MW] for all other "
                    "processes."
                ),
            ),
            "OPEX (fix)": st.column_config.NumberColumn(
                format="%.0f USD/[unit]",
                min_value=0,
                help=(
                    "unit is [t] for Green iron reduction and [MW] for all other "
                    "processes."
                ),
            ),
        }
        column_config.update(custom_column_config)

    if data_type == "dac_and_desalination":
        index = "process_code"
        columns = "parameter_code"
        missing_index_name = "source_region_code"
        missing_index_value = None
        column_config = {
            "CAPEX": st.column_config.NumberColumn(format="%.5f USD/kg", min_value=0),
            "OPEX (fix)": st.column_config.NumberColumn(
                format="%.5f USD/kg", min_value=0
            ),
            "efficiency": st.column_config.NumberColumn(
                format="%.2f", min_value=0, max_value=1
            ),
            "lifetime / amortization period": st.column_config.NumberColumn(
                format="%.0f a",
                min_value=0,
                help=read_markdown_file("md/helptext_columns_lifetime.md"),
            ),
        }

    if data_type == "WACC":
        index = "source_region_code"
        columns = "parameter_code"
        missing_index_name = "parameter_code"
        missing_index_value = "WACC"
        column_config = {
            c: st.column_config.NumberColumn(
                format="%.2f %%", min_value=0, max_value=100
            )
            for c in df.columns
        }

    if data_type == "CAPEX":
        index = "source_region_code"
        columns = "process_code"
        missing_index_name = "parameter_code"
        missing_index_value = "CAPEX"
        column_config = {
            c: st.column_config.NumberColumn(format="%.0f USD/kW", min_value=0)
            for c in df.columns
        }

    if data_type == "full load hours":
        index = "source_region_code"
        columns = "process_code"
        missing_index_name = "parameter_code"
        missing_index_value = "full load hours"
        column_config = {
            c: st.column_config.NumberColumn(
                format="%.0f h/a", min_value=0, max_value=8760
            )
            for c in df.columns
        }

    if data_type == "specific_costs":
        index = "flow_code"
        columns = "parameter_code"
        missing_index_name = None
        missing_index_value = None
        column_config = get_column_config()

    if data_type == "conversion_coefficients":
        index = "process_code"
        columns = "flow_code"
        missing_index_name = "parameter_code"
        missing_index_value = "conversion factors"
        column_config = get_column_config()

    if data_type == "storage":
        column_config["OPEX (fix)"] = st.column_config.NumberColumn(
            format="%.2f USD/kW", min_value=0
        )

    df = change_index_names(df)

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        if data_type == "full load hours":
            st.info("Full load hours data cannot be modified.")
            st.dataframe(
                df,
                use_container_width=True,
                column_config=column_config,
            )
        else:
            df = _form_data_editor(
                key,
                df,
                df_orig,
                index,
                columns,
                missing_index_name,
                missing_index_value,
                column_config,
            )

    else:
        st.dataframe(
            df,
            use_container_width=True,
            column_config=column_config,
        )

    scenario = st.session_state["scenario"].lower()
    scenario = scenario.replace(")", "").replace("(", "")
    fn = f"{key}_{scenario}".replace(" ", "_")
    prepare_and_download_df_as_excel(df, filename=fn)

    return df


def what_is_a_boxplot():
    with st.popover("What is a boxplot?"):
        st.image("img/boxplot_explanation.png")
