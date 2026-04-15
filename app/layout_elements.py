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
from ptxboa.static import ToolVersionColorType


def display_results_bar_and_table(
    df: pd.DataFrame,
    df_without_user_changes: pd.DataFrame,
    key: str,
    titlestring: str,
    key_suffix: str = "",
    output_unit: str | None = None,
    default_select: int = 0,
    default_manual_select: str | None = None,
    help_string: str | None = None,
    x_label_mapping: dict[str, str] | None = None,
    xaxis_title: str | None = None,
    tool_version_color: ToolVersionColorType = "green",
    data_type: Literal["costs", "emissions"] = "costs",
    sorting: Literal["toggle", "ascending", "off"] = "toggle",
    allow_diff_view: bool = True,
):
    """Display costs/emissions as table and bar chart."""
    if x_label_mapping is None:
        x_label_mapping = {}

    if data_type == "costs":
        min_10_label = "Cheapest 10"
        if output_unit is None:
            output_unit: str = st.session_state["output_unit"]

    if data_type == "emissions":
        min_10_label = "Lowest 10"
        if output_unit is None:
            output_unit: str = st.session_state["emissions_output_unit"]

    if sorting == "off":
        sort_ascending = False
    if sorting == "ascending":
        sort_ascending = True

    key_suffix = key_suffix.lower().replace(" ", "_")
    st.subheader(titlestring)

    if help_string is not None:
        st.markdown(help_string)

    c1, c2 = st.columns(2)

    # select which dataset to display:
    if st.session_state["user_changes_df"] is not None:
        if allow_diff_view:
            data_view_options = [
                "With Modifications",
                "Without Modifications",
                "Difference",
            ]
        else:
            data_view_options = [
                "With Modifications",
                "Without Modifications",
            ]
        with c2:
            st.info("Input data has been modified. Select which data to display.")
            select_data = st.radio(
                "Data to display",
                data_view_options,
                horizontal=True,
                key=f"select_user_modificatons_data_{key}_{key_suffix}",
            )
        if select_data == "With Modifications":
            df_res = df
        if select_data == "Without Modifications":
            df_res = df_without_user_changes
        if select_data == "Difference":
            df_res = df - df_without_user_changes
    else:
        df_res = df.copy()

    if default_manual_select is None:
        default_manual_select = df_res.index.values

    with c1:
        if len(df_res) < 7:
            show_which_data = "All"
        else:
            if len(df_res) > 13:
                select_options = [
                    "All",
                    "Manual selection",
                    min_10_label,
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
            with st.expander("Manual selection", expanded=True):
                ind_select = st.pills(
                    "Select elements:",
                    df_res.index.values,
                    default=default_manual_select,
                    key=f"select_data_{key}_{key_suffix}",
                    label_visibility="collapsed",
                    selection_mode="multi",
                    format_func=lambda k: x_label_mapping.get(k, k),
                )
            df_res = df_res.loc[ind_select]

        if show_which_data == min_10_label:
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

        if show_which_data != min_10_label and sorting == "toggle":
            sort_ascending = st.toggle(
                f"Sort by total {data_type}?",
                value=True,
                key=f"sort_data_{key}_{key_suffix}",
            )

    if len(df_res) == 0:
        st.warning("No data selected.")
        return

    if sort_ascending:
        df_res = df_res.sort_values(["Total"], ascending=True)

    if x_label_mapping:
        df_res = df_res.rename(index=x_label_mapping)
        current_selection = x_label_mapping.get(
            st.session_state[key], st.session_state[key]
        )
    else:
        current_selection = st.session_state[key]

    # fix index names
    change_index_names(df_res)

    # create graph:
    fig = create_bar_chart_costs(
        df_res,
        current_selection=current_selection,
        output_unit=output_unit,
    )
    if xaxis_title is not None:
        fig.update_layout(xaxis_title=xaxis_title)

    st.plotly_chart(fig, width="stretch")

    if output_unit.endswith("/MWh") and st.session_state["output_unit"].endswith("/t"):
        unit_note = (
            "The output unit is set to per MWh in order to compare products"
            " with different energy densities. "
        )
    else:
        unit_note = ""

    # add explainer for costs by supply chain comparison:
    if key == "chain" and tool_version_color == "green":
        green_iron_note = (
            "Green Iron is not shown in this comparison "
            "as it is not an energy carrier. "
        )
    else:
        green_iron_note = ""

    if unit_note or green_iron_note:
        st.caption(f"**Note**: {unit_note}{green_iron_note}")

    with st.expander("**Data**"):
        column_config = config_number_columns(df_res, format=f"%.1f {output_unit}")
        # remove <br> html tags from dataframe index
        df_res.index = df_res.index.str.replace("<br>", " ")
        st.dataframe(df_res, width="stretch", column_config=column_config)
        fn = f"{data_type}_per_{key}_{key_suffix}".strip("_")
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
                Agora Industry<br/>
                Anna-Louisa-Karsch-Str. 2<br/>
                D-10178 Berlin<br/>
                www.agora-industry.org
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                ##### Authors
                Christoph Heinemann<br/>
                Roman Mendelevitch<br/>
                Markus Haller<br/>
                Christian Winger<br/>
                Johannes Aschauer<br/>
                Susanne Krieger<br/>
                Katharina Göckeler<br/>
                """,
                unsafe_allow_html=True,
            )

        # TODO: fix uneven height and vertical alignment of logos
        c0, c1, c2, c3, c4, c5 = st.columns(
            [1, 2, 2, 2, 2, 1],
            gap="large",
        )
        with c1:
            st.image("img/Agora_Industry_logo_612x306.png")
        with c2:
            st.image("img/agora-energiewende_logo_612x306.png")
        with c3:
            st.image("img/oeko_logo_612x306.png")
        with c4:
            st.image("img/PtX-Hub_Logo_international_612x306.png")


def _form_data_editor(
    key,
    df,
    df_orig,
    index,
    columns,
    missing_index,
    column_config,
):
    if f"{key}_number" not in st.session_state:
        st.session_state[f"{key}_number"] = 0
    editor_key = f"{key}_{st.session_state[f'{key}_number']}"

    with st.form(key=f"{key}_form", border=False):
        st.info(
            (
                "You can edit data directly in the table. When done, click the "
                "**Register changes** button below. If you "
                "switch to one of the tabs where results are displayed, "
                "the results will be recalculated."
            )
        )

        st.form_submit_button(
            "Register changes",
            type="primary",
            on_click=register_user_changes,
            kwargs={
                "missing_index": missing_index,
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
            width="stretch",
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
        "Natural gas price",
    ],
    scope: Literal["world", "Argentina", "Morocco", "South Africa"],
    key: str,
    tool_version_color: ToolVersionColorType = "green",
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
    df = get_data_type_from_input_data(
        api, data_type=data_type, scope=scope, tool_version_color=tool_version_color
    )
    df_orig = df.copy()

    column_config = get_column_config()
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
        missing_index = {"source_region_code": None}

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
        missing_index = {"source_region_code": None}
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
        missing_index = {"parameter_code": "WACC"}
        column_config = {
            c: st.column_config.NumberColumn(
                format="%.2f %%", min_value=0, max_value=100
            )
            for c in df.columns
        }

    if data_type == "CAPEX":
        index = "source_region_code"
        columns = "process_code"
        missing_index = {"parameter_code": "CAPEX"}
        column_config = {
            c: st.column_config.NumberColumn(format="%.0f USD/kW", min_value=0)
            for c in df.columns
        }

    if data_type == "full load hours":
        index = "source_region_code"
        columns = "process_code"
        missing_index = {"parameter_code": "full load hours"}
        column_config = {
            c: st.column_config.NumberColumn(
                format="%.0f h/a", min_value=0, max_value=8760
            )
            for c in df.columns
        }

    if data_type == "specific_costs":
        index = "flow_code"
        columns = "parameter_code"
        missing_index = None
        column_config = get_column_config()

    if data_type == "conversion_coefficients":
        index = "process_code"
        columns = "flow_code"
        missing_index = {"parameter_code": "conversion factors"}
        column_config = get_column_config()

    if data_type == "storage":
        column_config["OPEX (fix)"] = st.column_config.NumberColumn(
            format="%.2f USD/kW", min_value=0
        )

    if data_type == "Natural gas production costs":
        index = "source_region_code"
        columns = "parameter_code"
        missing_index = {"process_code": "production of natural gas (blue)"}
        column_config["OPEX (other variable)"] = st.column_config.NumberColumn(
            label="production costs",
            format="%.4f USD/kWh",
            min_value=0,
        )

    if data_type == "Natural gas production losses":
        index = "source_region_code"
        columns = "parameter_code"
        missing_index = {
            "process_code": "production of natural gas (blue)",
            "flow_code": "natural gas (gasous)",
        }
        column_config["losses (own fuel)"] = st.column_config.NumberColumn(
            format="%.4f [fraction]",
            min_value=0,
        )

    if data_type == "Natural gas price":
        index = "source_region_code"
        columns = "parameter_code"
        missing_index = {"flow_code": "natural gas (gasous)"}

    df = change_index_names(df)

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        if data_type == "full load hours":
            st.info("Full load hours data cannot be modified.")
            st.dataframe(
                df,
                width="stretch",
                column_config=column_config,
            )
        else:
            df = _form_data_editor(
                key,
                df,
                df_orig,
                index,
                columns,
                missing_index,
                column_config,
            )

    else:
        st.dataframe(
            df,
            width="stretch",
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


def report_processes_contained_in_process_result_type(
    _api: PtxboaAPI, tool_version_color: ToolVersionColorType
):
    data = (
        _api.get_dimension("process", tool_version_color=tool_version_color)
        .loc[:, ["process_name", "result_process_type"]]
        .groupby("result_process_type")
        .agg(list)
        .to_dict()["process_name"]
    )
    with st.expander("Aggregated process categories and associated processes"):
        for process_result_type, processes in data.items():
            with st.expander(process_result_type):
                section = []
                for p in processes:
                    section.append(f"- {p}")
                st.markdown("\n".join(section))
