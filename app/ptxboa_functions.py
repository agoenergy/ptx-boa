# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""
import logging
from pathlib import Path
from typing import Literal

import pandas as pd
import streamlit as st

from ptxboa.api import PtxboaAPI
from ptxboa.utils import is_test


@st.cache_data(show_spinner=False)
def calculate_results_single(
    _api: PtxboaAPI,
    settings: dict,
    user_data: pd.DataFrame | None = None,
    optimize_flh: bool = True,
    use_user_data_for_optimize_flh: bool = False,
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
    res, _metadata = _api.calculate(
        user_data=user_data,
        **settings,
        optimize_flh=optimize_flh,
        use_user_data_for_optimize_flh=use_user_data_for_optimize_flh,
    )

    return res


def calculate_results_list(
    api: PtxboaAPI,
    parameter_to_change: str,
    parameter_list: list = None,
    override_session_state: dict | None = None,
    apply_user_data: bool = True,
    optimize_flh: bool = True,  # @markushal: use FLH optimizer by default
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

    # in test environment: do not optimize by default
    # NOTE: does not work in global, must be called here in a function
    optimize_flh = not is_test()

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

    # drop Green Iron if comparing chains (because it is not an energy carrier)
    if parameter_to_change == "chain":
        parameter_list = parameter_list[~parameter_list.str.startswith("Green Iron")]

    res_list = []
    for parameter in parameter_list:
        settings.update({parameter_to_change: parameter})

        # consider user data in optimization only for parameter set in session state
        if st.session_state[parameter_to_change] == parameter:
            use_user_data_for_optimize_flh = True
        else:
            use_user_data_for_optimize_flh = False

        # catch all api errors so that the tool is stable
        try:
            res_single = calculate_results_single(
                api,
                settings,
                user_data=(
                    st.session_state["user_changes_df"] if apply_user_data else None
                ),
                optimize_flh=optimize_flh,
                use_user_data_for_optimize_flh=use_user_data_for_optimize_flh,
            )
            res_list.append(res_single)
        except Exception as exc:
            logging.info(f"could not get data: {exc}")

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
        "WACC",
        "specific_costs",
        "conversion_coefficients",
        "dac_and_desalination",
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
        "reconversion_processes", "CAPEX", "full load hours", "WACC",
        "specific costs", "conversion_coefficients" and "dac_and_desalination".
    scope : Literal[None, "world", "Argentina", "Morocco", "South Africa"]
        The regional scope. Is automatically set to None for data of
        data type "conversion_processes" and "transportation_processes" which is not
        region specific.

    Returns
    -------
    pd.DataFrame
    """
    if data_type == "full load hours":
        input_data = api.get_optimization_flh_input_data()
        df = subset_and_pivot_input_data(
            input_data,
            source_region_code=None,
            parameter_code=None,
            process_code=None,
            index="source_region",
            columns="res_gen",
            values="value",
        )
        if scope == "world":
            df = remove_subregions(
                api=api, df=df, country_name=st.session_state["country"]
            )
        if scope in ["Argentina", "Morocco", "South Africa"]:
            df = select_subregions(df, scope)
        return df

    input_data = api.get_input_data(
        st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    if data_type in [
        "electricity_generation",
        "conversion_processes",
        "transportation_processes",
        "reconversion_processes",
        "dac_and_desalination",
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
        parameter_code = ["specific costs"]
        process_code = [""]

    if data_type == "conversion_coefficients":
        scope = None
        source_region_code = [""]
        index = "process_code"
        columns = "flow_code"
        parameter_code = ["conversion factors"]
        process_code = input_data.loc[
            input_data["parameter_code"] == "conversion factors", "process_code"
        ].unique()

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
            ~processes["is_transport"]
            & ~processes["is_re_generation"]
            & ~processes["is_secondary"],
            "process_name",
        ].to_list()

    if data_type == "dac_and_desalination":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
        ]
        process_code = processes.loc[
            processes["is_secondary"], "process_name"
        ].to_list()

    if data_type == "transportation_processes":
        parameter_code = [
            "losses (own fuel, transport)",
            "levelized costs",
            "lifetime / amortization period",
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

    if data_type in ["CAPEX", "WACC"]:
        source_region_code = None
        parameter_code = [data_type]
        index = "source_region_code"

    if data_type == "WACC":
        columns = "parameter_code"
        process_code = [""]

    if data_type == "CAPEX":
        columns = "process_code"
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
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

    # remove electricity from specific costs
    if data_type == "specific_costs":
        df = df[~(df.index == "electricity")]

    if scope == "world":
        df = remove_subregions(api=api, df=df, country_name=st.session_state["country"])
    if scope in ["Argentina", "Morocco", "South Africa"]:
        df = select_subregions(df, scope)

    # transform data to match unit [%] for 'WACC' and 'efficieny'
    if data_type == "WACC":
        df = df * 100

    if "efficiency" in df.columns:
        df["efficiency"] = df["efficiency"] * 100

    return df


def remove_subregions(
    api: PtxboaAPI, df: pd.DataFrame, country_name: str, keep: str | None = None
):
    """Remove subregions from a dataframe.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    df : pd.DataFrame
        pandas DataFrame with list of regions as index.

    country_name : str
        name of target country. Is removed from region list if it is also in there.

    keep : str or None, by default None
        can be used to keep data for a specific subregion

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

    # sometimes, not all regions exist
    region_list_without_subregions = [
        r for r in region_list_without_subregions if r in df.index
    ]

    if keep is not None:
        region_list_without_subregions.append(keep)

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


def config_number_columns(df: pd.DataFrame, **kwargs) -> {}:
    """Create number column config info for st.dataframe() or st.data_editor."""
    column_config_all = {}
    for c in df.columns:
        column_config_all[c] = st.column_config.NumberColumn(
            **kwargs,
        )

    return column_config_all


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
            format="%.2f %%", min_value=0, max_value=100
        ),
        "lifetime / amortization period": st.column_config.NumberColumn(
            format="%.0f a",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_lifetime.md"),
        ),
        "levelized costs": st.column_config.NumberColumn(
            format="%.2e USD/([unit] km)",
            min_value=0,
            help=(
                "unit is [t] for Green iron ship (bunker fuel consumption) and [MW] "
                "for all other processes."
            ),
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
        "bunker fuel": st.column_config.NumberColumn(
            format="%.2e",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_bunker_fuel.md"),
        ),
        "FT e-fuels": st.column_config.NumberColumn(
            format="%.2e",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_ft_e_fuels.md"),
        ),
        "carbon dioxide": st.column_config.NumberColumn(
            format="%.3f",
            help=read_markdown_file("md/helptext_columns_carbon_dioxide.md"),
        ),
        "electricity": st.column_config.NumberColumn(
            format="%.3f",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_electricity.md"),
        ),
        "heat": st.column_config.NumberColumn(
            format="%.3f",
            help=read_markdown_file("md/helptext_columns_heat.md"),
        ),
        "nitrogen": st.column_config.NumberColumn(
            format="%.3f",
            min_value=0,
            help=read_markdown_file("md/helptext_columns_nitrogen.md"),
        ),
        "water": st.column_config.NumberColumn(
            format="%.3f",
            help=read_markdown_file("md/helptext_columns_water.md"),
        ),
    }
    return column_config


def change_index_names(df: pd.DataFrame, mapping: dict | None = None) -> pd.DataFrame:
    """
    Change the index name of cost results or input data dataframes.

    Only call this just befor you display any data, not before any transformation
    or pivot actions.

    https://stackoverflow.com/a/19851521

    If mapping is None, default mappings for input_data and cost_results data is
    used.
    """
    if mapping is None:
        mapping = {
            "process_code": "Process",
            "source_region_code": "Source region",
            "region": "Source region",
            "source_region": "Source region",
            "scenario": "Scenario",
            "res_gen": "RE source",
            "chain": "Chain",
            "flow_code": "Carrier/Material",
        }
    new_idx_names = [mapping.get(i, i) for i in df.index.names]
    df.index.names = new_idx_names
    return df


def check_if_input_is_needed(api: PtxboaAPI, flow_code: str) -> bool:
    """Check if a certain input is required by the selected process chain."""
    # get list of processes in selected chain:
    process_codes = (
        api.get_dimension("chain").loc[st.session_state["chain"]][:-1].to_list()
    )
    process_codes = [p for p in process_codes if p != ""]

    # get list of conversion coefficients for these processes:
    df = api.get_input_data(scenario=st.session_state["scenario"], long_names=False)
    flow_codes = df.loc[
        (df["process_code"].isin(process_codes)) & (df["parameter_code"] == "CONV"),
        "flow_code",
    ].to_list()

    return flow_code in flow_codes
