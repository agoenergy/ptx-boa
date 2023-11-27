# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""

from typing import Literal

import pandas as pd
import streamlit as st

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
    user_data: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Calculate results for source regions and one selected target country.

    Parameters
    ----------
    _api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.
    parameter_to_change : str
        element of settings for which a list of values is to be used.
    parameter_list : list or None
        The values of ``parameter_to_change`` for which the results are calculated.
        If None, all values available in the API will be used.

    Returns
    -------
    pd.DataFrame
        same format as for :meth:`~ptxboa.api.PtxboaAPI.calculate()`
    """
    res_list = []

    if parameter_list is None:
        parameter_list = api.get_dimension(parameter_to_change).index

    # copy settings from session_state:
    settings = {}
    for key in [
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
    ]:
        settings[key] = st.session_state[key]

    for parameter in parameter_list:
        settings2 = settings.copy()
        settings2[parameter_to_change] = parameter
        res_single = calculate_results_single(api, settings2, user_data=user_data)
        res_list.append(res_single)
    res_details = pd.concat(res_list)

    return aggregate_costs(res_details)


def aggregate_costs(res_details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detailed costs."""
    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index="region", columns="process_type", values="values", aggfunc="sum"
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    return res


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


def reset_user_changes():
    """Reset all user changes."""
    if (
        not st.session_state["edit_input_data"]
        and st.session_state["user_changes_df"] is not None
    ):
        st.session_state["user_changes_df"] = None


def display_user_changes():
    """Display input data changes made by user."""
    if st.session_state["user_changes_df"] is not None:
        st.dataframe(
            st.session_state["user_changes_df"].style.format(precision=3),
            hide_index=True,
        )
    else:
        st.write("You have not changed any values yet.")


def display_and_edit_data_table(
    input_data: pd.DataFrame,
    missing_index_name: str,
    missing_index_value: str,
    source_region_code: list = None,
    parameter_code: list = None,
    process_code: list = None,
    index: str = "source_region_code",
    columns: str = "process_code",
    values: str = "value",
    column_config: dict = None,
    key_suffix: str = "",
) -> pd.DataFrame:
    """Display selected input data as 2D table, which can also be edited."""
    # filter data and reshape to wide format.
    df_tab = subset_and_pivot_input_data(
        input_data,
        source_region_code,
        parameter_code,
        process_code,
        index,
        columns,
        values,
    )

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        disabled = [index]
        key = (
            f"edit_input_data_{'_'.join(parameter_code).replace(' ', '_')}{key_suffix}"
        )
    else:
        disabled = True
        key = None

    # configure columns for display:
    if column_config is None:
        column_config_all = None
    else:
        column_config_all = config_number_columns(df_tab, **column_config)

    # display data:
    df_tab = st.data_editor(
        df_tab,
        use_container_width=True,
        key=key,
        num_rows="fixed",
        disabled=disabled,
        column_config=column_config_all,
        on_change=register_user_changes,
        kwargs={
            "missing_index_name": missing_index_name,
            "missing_index_value": missing_index_value,
            "index": index,
            "columns": columns,
            "values": values,
            "df_tab": df_tab,
            "key": key,
        },
    )
    if st.session_state["edit_input_data"]:
        st.markdown("You can edit data directly in the table!")
    return df_tab


def register_user_changes(
    missing_index_name: str,
    missing_index_value: str,
    index: str,
    columns: str,
    values: str,
    df_tab: pd.DataFrame,
    key: str,
):
    """
    Register all user changes in the session state variable "user_changes_df".

    If a change already has been recorded, use the lastest value.
    """
    # convert session state dict to dataframe:
    # Create a list of dictionaries
    data_dict = st.session_state[key]["edited_rows"]
    data_list = []

    for k, v in data_dict.items():
        for c_name, value in v.items():
            data_list.append({index: k, columns: c_name, values: value})

    # Convert the list to a DataFrame
    res = pd.DataFrame(data_list)

    # add missing key (the info that is not contained in the 2D table):
    res[missing_index_name] = missing_index_value

    # Replace the 'id' values with the corresponding index elements from df_tab
    res[index] = res[index].map(lambda x: df_tab.index[x])

    if st.session_state["user_changes_df"] is None:
        st.session_state["user_changes_df"] = pd.DataFrame(
            columns=["source_region_code", "process_code", "parameter_code", "value"]
        )

    # only track the last changes if a duplicate entry is found.
    st.session_state["user_changes_df"] = pd.concat(
        [st.session_state["user_changes_df"], res]
    ).drop_duplicates(
        subset=["source_region_code", "process_code", "parameter_code"], keep="last"
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
        "conversion_processes",
        "transportation_processes",
        "CAPEX",
        "full load hours",
        "interest rate",
    ],
    scope: Literal["world", "Argentina", "Morocco", "South Africa"],
    key: str,
):
    input_data = api.get_input_data(
        st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    if data_type in ["conversion_processes", "transportation_processes"]:
        scope = "non_region_specific_data"
        missing_index_name = "source_region_code"
        missing_index_value = None
        index = "process_code"
        columns = "parameter_code"
        processes = api.get_dimension("process")
        source_region_code = None
        values = "value"
        column_config = None

        process_code = processes.loc[
            ~processes["is_transport"], "process_name"
        ].to_list()

    if data_type == "conversion_processes":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ]
        process_code = processes.loc[
            ~processes["is_transport"], "process_name"
        ].to_list()

    if data_type == "transportation_processes":
        parameter_code = [
            "losses (own fuel, transport)",
            "levelized costs",
            "lifetime / amortization period",
            # FIXME: add bunker fuel consumption
        ]
        process_code = processes.loc[
            processes["is_transport"], "process_name"
        ].to_list()

    if data_type in ["CAPEX", "full load hours", "interest_rate"]:
        raise NotImplementedError

    if scope == "non_region_specific_data":
        source_region_code = [""]

    df = subset_and_pivot_input_data(
        input_data,
        source_region_code,
        parameter_code,
        process_code,
        index,
        columns,
        values,
    )

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        disabled = [index]
    else:
        disabled = True

    # configure columns for display:
    if column_config is None:
        column_config = None
    else:
        column_config = config_number_columns(df, **column_config)

    df = st.data_editor(
        df,
        use_container_width=True,
        key=key,
        num_rows="fixed",
        disabled=disabled,
        column_config=column_config,
        on_change=register_user_changes,
        kwargs={
            "missing_index_name": missing_index_name,
            "missing_index_value": missing_index_value,
            "index": index,
            "columns": columns,
            "values": values,
            "df_tab": df,
            "key": key,
        },
    )
    if st.session_state["edit_input_data"]:
        st.markdown("You can edit data directly in the table!")
    return df
