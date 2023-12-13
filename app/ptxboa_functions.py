# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd
import streamlit as st

from app.excel_download import prepare_and_download_df_as_excel
from ptxboa.api import PtxboaAPI


@st.cache_data()
def calculate_results_single(
    _api: PtxboaAPI,
    settings: dict,
    user_data: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate results for a single set of settings.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.

    Returns
    -------
    pd.DataFrame
        same format as for :meth:`~ptxboa.api.PtxboaAPI.calculate()`
    """
    res = _api.calculate(user_data=user_data, **settings)

    return res


def calculate_results_list(
    api: PtxboaAPI,
    parameter_to_change: str,
    parameter_list: list = None,
    override_session_state: dict | None = None,
    apply_user_data: bool = True,
) -> pd.DataFrame:
    """Calculate results for source regions and one selected target country.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    parameter_to_change : str
        element of settings for which a list of values is to be used.
    parameter_list : list or None
        The values of ``parameter_to_change`` for which the results are calculated.
        If None, all values available in the API will be used.
    override_session_state : dict or None
        pass a dict with custom values in order to change the calculation parameters
        obtained from st.session_state. I None, all parameters are taken from the
        session state. Keys of the dictionary must in "chain", "country",
        "output_unit", "region", "res_gen", "scenario", "secproc_co2",
        "secproc_water", "ship_own_fuel", "transport".
    apply_user_data: bool
        If true, apply user data modifications (default).
        If false, use only default scenario data.

    Returns
    -------
    pd.DataFrame
        wide format dataframe with index values from `parameter_to_change` and columns
        containing the different cost components and a column for total costs "Total".
    """
    setting_keys = [
        "chain",
        "country",
        "output_unit",
        "region",
        "res_gen",
        "scenario",
        "secproc_co2",
        "secproc_water",
        "ship_own_fuel",
        "transport",
    ]

    # copy settings from session_state:
    settings = {key: st.session_state[key] for key in setting_keys}

    # update settings from session state with custom values
    if override_session_state is not None:
        if not set(override_session_state.keys()).issubset(set(setting_keys)):
            msg = (
                f"keys in 'override_session_state' must be in dict_keys({setting_keys})"
                f" but are currently {override_session_state.keys()}"
            )
            raise ValueError(msg)
        settings.update(override_session_state)

    if parameter_list is None:
        parameter_list = api.get_dimension(parameter_to_change).index

    res_list = []
    for parameter in parameter_list:
        settings.update({parameter_to_change: parameter})
        res_single = calculate_results_single(
            api,
            settings,
            user_data=st.session_state["user_changes_df"] if apply_user_data else None,
        )
        res_list.append(res_single)
    res_details = pd.concat(res_list)

    return aggregate_costs(res_details, parameter_to_change)


def aggregate_costs(
    res_details: pd.DataFrame, parameter_to_change: str
) -> pd.DataFrame:
    """Aggregate detailed costs."""
    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index=parameter_to_change,
        columns="process_type",
        values="values",
        aggfunc="sum",
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    return sort_cost_type_columns_by_position_in_chain(res)


def sort_cost_type_columns_by_position_in_chain(df):
    """Change cost type column order to match the occurrence in a chain.

    This is necessary for the order of the colors in the stacked barplots (GH #150).

    Parameters
    ----------
    df : pd.DataFrame
        columns need to be in 'cost_type_order'

    Returns
    -------
    pd.DataFrame
        same data with changed order of columns.
    """
    #
    cost_type_order = [
        "Electricity generation",
        "Electrolysis",
        "Electricity and H2 storage",
        "Derivate production",
        "Heat",
        "Water",
        "Carbon",
        "Transportation (Pipeline)",
        "Transportation (Ship)",
        "Total",
    ]
    assert [c in cost_type_order for c in df.columns]
    cols = [c for c in cost_type_order if c in df.columns]
    return df[cols]


def subset_and_pivot_input_data(
    input_data: pd.DataFrame,
    source_region_code: list = None,
    parameter_code: list = None,
    process_code: list = None,
    index: str = "source_region_code",
    columns: str = "process_code",
    values: str = "value",
):
    """
    Reshapes and subsets input data.

    Parameters
    ----------
    input_data : pd.DataFrame
        obtained with :meth:`~ptxboa.api.PtxboaAPI.get_input_data`
    source_region_code : list, optional
        list for subsetting source regions, by default None
    parameter_code : list, optional
        list for subsetting parameter_codes, by default None
    process_code : list, optional
        list for subsetting process_codes, by default None
    index : str, optional
        index for `pivot_table()`, by default "source_region_code"
    columns : str, optional
        column for generating new columns in pivot_table, by default "process_code"
    values : str, optional
        values for `pivot_table()` , by default "value"

    Returns
    -------
    : pd.DataFrame
    """
    if source_region_code is not None:
        input_data = input_data.loc[
            input_data["source_region_code"].isin(source_region_code)
        ]
    if parameter_code is not None:
        input_data = input_data.loc[input_data["parameter_code"].isin(parameter_code)]
    if process_code is not None:
        input_data = input_data.loc[input_data["process_code"].isin(process_code)]

    reshaped = input_data.pivot_table(
        index=index, columns=columns, values=values, aggfunc="sum"
    )
    return reshaped


def get_data_type_from_input_data(
    api: PtxboaAPI,
    data_type: Literal[
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes",
        "CAPEX",
        "full load hours",
        "interest rate",
        "specific_costs",
    ],
    scope: Literal[None, "world", "Argentina", "Morocco", "South Africa"],
) -> pd.DataFrame:
    """
    Get a pivoted table from input data based on data type and regional scope.

    This function internally calls :func:`subset_and_pivot_input_data` and makes
    assumptions on how the input data set should be filtered based on selected
    data type and scope.

    Parameters
    ----------
    api : PtxboaAPI
        api class instance
    data_type : str
        the data type which should be selected. Needs to be one of
        "electricity_generation", "conversion_processes", "transportation_processes",
        "reconversion_processes", "CAPEX", "full load hours", "interest rate",
        and "specific costs".
    scope : Literal[None, "world", "Argentina", "Morocco", "South Africa"]
        The regional scope. Is automatically set to None for data of
        data type "conversion_processes" and "transportation_processes" which is not
        region specific.

    Returns
    -------
    pd.DataFrame
    """
    input_data = api.get_input_data(
        st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    if data_type in [
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes",
    ]:
        scope = None
        source_region_code = [""]
        index = "process_code"
        columns = "parameter_code"
        processes = api.get_dimension("process")

    if data_type == "specific_costs":
        scope = None
        source_region_code = [""]
        index = "flow_code"
        columns = "parameter_code"
        processes = [""]
        parameter_code = ["specific costs"]
        process_code = [""]

    if data_type == "electricity_generation":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ]
        process_code = processes.loc[
            processes["is_re_generation"], "process_name"
        ].to_list()

    if data_type == "conversion_processes":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ]
        process_code = processes.loc[
            ~processes["is_transport"] & ~processes["is_re_generation"], "process_name"
        ].to_list()

    if data_type == "transportation_processes":
        parameter_code = [
            "losses (own fuel, transport)",
            "levelized costs",
            "lifetime / amortization period",
            # FIXME: add bunker fuel consumption
        ]
        process_code = processes.loc[
            processes["is_transport"] & ~processes["is_transformation"], "process_name"
        ].to_list()

    if data_type == "reconversion_processes":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ]
        process_code = processes.loc[
            processes["is_transport"] & processes["is_transformation"], "process_name"
        ].to_list()

    if data_type in ["CAPEX", "full load hours", "interest rate"]:
        source_region_code = None
        parameter_code = [data_type]
        index = "source_region_code"

    if data_type == "interest rate":
        columns = "parameter_code"
        process_code = [""]

    if data_type in ["CAPEX", "full load hours"]:
        columns = "process_code"
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]

    df = subset_and_pivot_input_data(
        input_data,
        source_region_code=source_region_code,
        parameter_code=parameter_code,
        process_code=process_code,
        index=index,
        columns=columns,
        values="value",
    )

    if scope == "world":
        df = remove_subregions(api=api, df=df, country_name=st.session_state["country"])
    if scope in ["Argentina", "Morocco", "South Africa"]:
        df = select_subregions(df, scope)

    return df


def remove_subregions(api: PtxboaAPI, df: pd.DataFrame, country_name: str):
    """Remove subregions from a dataframe.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    df : pd.DataFrame
        pandas DataFrame with list of regions as index.

    country_name : str
        name of target country. Is removed from region list if it is also in there.

    Returns
    -------
    pandas DataFrame with subregions removed from index.
    """
    # do not show subregions:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )

    # ensure that target country is not in list of regions:
    if country_name in region_list_without_subregions:
        region_list_without_subregions.remove(country_name)

    df = df.loc[region_list_without_subregions]

    return df


def select_subregions(
    df: pd.DataFrame, deep_dive_country: Literal["Argentina", "Morocco", "South Africa"]
) -> pd.DataFrame:
    """
    Only select rows corresponding to subregions of a deep dive country.

    Parameters
    ----------
    df : pd.DataFrame
        pandas DataFrame with list of regions as index.
    deep_dive_country : str in {"Argentina", "Morocco", "South Africa"}


    Returns
    -------
    pd.DataFrame
    """
    df = df.copy().loc[df.index.str.startswith(f"{deep_dive_country} ("), :]
    return df


def reset_user_changes():
    """Reset all user changes."""
    if (
        not st.session_state["edit_input_data"]
        and st.session_state["user_changes_df"] is not None
    ):
        st.session_state["user_changes_df"] = None


def display_user_changes(api):
    """Display input data changes made by user."""
    if st.session_state["user_changes_df"] is not None:
        df = st.session_state["user_changes_df"].copy()
        parameters = api.get_dimension("parameter")
        df["Unit"] = df["parameter_code"].map(
            pd.Series(parameters["unit"].tolist(), index=parameters["parameter_name"])
        )
        st.dataframe(
            df.rename(
                columns={
                    "source_region_code": "Source Region",
                    "process_code": "Process",
                    "parameter_code": "Parameter",
                    "flow_code": "Carrier/Material",
                    "value": "Value",
                }
            ).style.format(precision=3),
            hide_index=True,
        )
    else:
        st.write("You have not changed any values yet.")


def register_user_changes(
    missing_index_name: str,
    missing_index_value: str,
    index: str,
    columns: str,
    values: str,
    df_tab: pd.DataFrame,
    df_orig: pd.DataFrame,
    key: str,
    editor_key: str,
):
    """
    Register all user changes in the session state variable "user_changes_df".

    If a change already has been recorded, use the lastest value.
    """
    # convert session state dict to dataframe:
    # Create a list of dictionaries
    data_dict = st.session_state[editor_key]["edited_rows"]
    if any(data_dict.values()):
        data_list = []

        rejected_changes = False
        for k, v in data_dict.items():
            for c_name, value in v.items():
                if np.isnan(df_orig.iloc[k, :][c_name]):
                    msg = (
                        f":exclamation: Cannot modify empty value '{c_name}' "
                        f"for '{df_orig.index[k]}'"
                    )
                    st.toast(msg)
                    rejected_changes = True
                else:
                    data_list.append({index: k, columns: c_name, values: value})

        if rejected_changes:
            # modify key number
            st.session_state[f"{key}_number"] += 1

        if len(data_list) == 0:
            return

        # Convert the list to a DataFrame
        res = pd.DataFrame(data_list)

        # add missing key (the info that is not contained in the 2D table):
        if missing_index_name is not None or missing_index_value is not None:
            res[missing_index_name] = missing_index_value

        # Replace the 'id' values with the corresponding index elements from df_tab
        res[index] = res[index].map(lambda x: df_tab.index[x])

        if st.session_state["user_changes_df"] is None:
            st.session_state["user_changes_df"] = pd.DataFrame(
                columns=[
                    "source_region_code",
                    "process_code",
                    "parameter_code",
                    "flow_code",
                    "value",
                ]
            )

        # only track the last changes if a duplicate entry is found.
        st.session_state["user_changes_df"] = pd.concat(
            [st.session_state["user_changes_df"], res]
        ).drop_duplicates(
            subset=[
                "source_region_code",
                "process_code",
                "parameter_code",
                "flow_code",
            ],
            keep="last",
        )


def config_number_columns(df: pd.DataFrame, **kwargs) -> {}:
    """Create number column config info for st.dataframe() or st.data_editor."""
    column_config_all = {}
    for c in df.columns:
        column_config_all[c] = st.column_config.NumberColumn(
            **kwargs,
        )

    return column_config_all


def display_and_edit_input_data(
    api: PtxboaAPI,
    data_type: Literal[
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes" "CAPEX",
        "full load hours",
        "interest rate",
        "specific_costs",
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
        "reconversion_processes", "CAPEX", "full load hours", "interest rate",
        and "specific costs".
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
    ]:
        index = "process_code"
        columns = "parameter_code"
        missing_index_name = "source_region_code"
        missing_index_value = None
        column_config = get_column_config()

    if data_type == "interest rate":
        index = "source_region_code"
        columns = "parameter_code"
        missing_index_name = "parameter_code"
        missing_index_value = "interest rate"
        column_config = {
            c: st.column_config.NumberColumn(format="%.3f", min_value=0, max_value=1)
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

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        if f"{key}_number" not in st.session_state:
            st.session_state[f"{key}_number"] = 0
        editor_key = f"{key}_{st.session_state[f'{key}_number']}"

        with st.form(key=f"{key}_form", border=False):
            st.info(
                (
                    "You can edit data directly in the table. When done, click the "
                    "**Apply Changes** button below to rerun calculations."
                )
            )

            st.form_submit_button(
                "Apply Changes",
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


def move_to_tab(tab_name):
    """
    Move to a certain tab within a callback.

    Increment the session state variable "tab_key" by 1.

    Parameters
    ----------
    tab_name : str
    """
    old_tab_key_nb = int(st.session_state["tab_key"].replace("tab_key_", ""))
    st.session_state["tab_key"] = f"tab_key_{old_tab_key_nb + 1}"
    st.session_state[st.session_state["tab_key"]] = tab_name


def read_markdown_file(markdown_file: str) -> str:
    """Import markdown file as string."""
    return Path(markdown_file).read_text(encoding="UTF-8")


def get_region_from_subregion(subregion: str) -> str:
    """
    For a subregion, get the name of the region it belongs to.

    If subregion is not a subregion, return its own name.
    """
    region = subregion.split(" (")[0]
    return region


def get_column_config() -> dict:
    """Define column configuration for dataframe display."""
    column_config = {
        "CAPEX": st.column_config.NumberColumn(format="%.0f USD/kW", min_value=0),
        "OPEX (fix)": st.column_config.NumberColumn(format="%.0f USD/kW", min_value=0),
        "efficiency": st.column_config.NumberColumn(
            format="%.2f", min_value=0, max_value=1
        ),
        "lifetime / amortization period": st.column_config.NumberColumn(
            format="%.0f a",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_lifetime.md"),
        ),
        "levelized costs": st.column_config.NumberColumn(
            format="%.2e USD/(kW km)", min_value=0
        ),
        "losses (own fuel, transport)": st.column_config.NumberColumn(
            format="%.2e fraction per km",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_losses.md"),
        ),
        "specific costs": st.column_config.NumberColumn(
            format="%.3f [various units]",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_specific_costs.md"),
        ),
    }
    return column_config
