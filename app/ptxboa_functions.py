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
        res_single = calculate_results_single(
            api,
            settings2,
            user_data=st.session_state["user_changes_df"],
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
        "conversion_processes",
        "transportation_processes",
        "CAPEX",
        "full load hours",
        "interest rate",
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
        "conversion_processes", "transportation_processes", "CAPEX", "full load hours",
        and "interest rate".
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

    if data_type in ["conversion_processes", "transportation_processes"]:
        scope = None
        source_region_code = [""]
        index = "process_code"
        columns = "parameter_code"
        processes = api.get_dimension("process")

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
    key: str,
):
    """
    Register all user changes in the session state variable "user_changes_df".

    If a change already has been recorded, use the lastest value.
    """
    # convert session state dict to dataframe:
    # Create a list of dictionaries
    data_dict = st.session_state[key]["edited_rows"]
    if any(data_dict):
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
                columns=[
                    "source_region_code",
                    "process_code",
                    "parameter_code",
                    "value",
                ]
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
        "conversion_processes", "transportation_processes", "CAPEX", "full load hours",
        and "interest rate".
    scope : Literal[None, "world", "Argentina", "Morocco", "South Africa"]
        The regional scope. Is automatically set to None for data of
        data type "conversion_processes" and "transportation_processes" which is not
        region specific.
    key : str
        A key for the data editing streamlit widget. Need to be unique.

    Returns
    -------
    pd.DataFrame
    """
    df = get_data_type_from_input_data(api, data_type=data_type, scope=scope)

    if data_type in ["conversion_processes", "transportation_processes"]:
        index = "process_code"
        columns = "parameter_code"
        missing_index_name = "source_region_code"
        missing_index_value = None
        column_config = None

    if data_type == "conversion_processes":
        column_config = {
            "CAPEX": st.column_config.NumberColumn(format="%.0f USD/kW", min_value=0),
            "OPEX (fix)": st.column_config.NumberColumn(
                format="%.0f USD/kW", min_value=0
            ),
            "efficiency": st.column_config.NumberColumn(
                format="%.2f", min_value=0, max_value=1
            ),
            "lifetime / amortization period": st.column_config.NumberColumn(
                format="%.0f a", min_value=0
            ),
        }

    if data_type == "transportation_processes":
        column_config = {
            "levelized_costs": st.column_config.NumberColumn(
                format="%.0f USD/kW", min_value=0
            ),
            "OPEX (fix)": st.column_config.NumberColumn(
                format="%.0f USD/kW", min_value=0
            ),
            "efficiency": st.column_config.NumberColumn(
                format="%.2f", min_value=0, max_value=1
            ),
            "lifetime / amortization period": st.column_config.NumberColumn(
                format="%.0f a", min_value=0
            ),
        }

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

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        with st.form(key=f"{key}_form"):
            st.info(
                (
                    "You can edit data directly in the table. When done, click the "
                    "**Apply Changes** button below to rerun calculations."
                )
            )
            df = st.data_editor(
                df,
                use_container_width=True,
                key=key,
                num_rows="fixed",
                disabled=[index],
                column_config=column_config,
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
                    "key": key,
                },
            )
    else:
        st.dataframe(
            df,
            use_container_width=True,
            column_config=column_config,
        )

    return df
