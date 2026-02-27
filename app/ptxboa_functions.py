# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Literal, Optional

import pandas as pd
import streamlit as st

from ptxboa.api import ApiCalculateResult, PtxboaAPI
from ptxboa.static import (
    ChainNameType,
    OutputUnitType,
    ResGenType,
    ScenarioType,
    SecProcCO2Type,
    SecProcH2OType,
    SourceRegionNameType,
    TargetCountryNameType,
    ToolVersionColorType,
    TransportType,
)
from ptxboa.utils import is_test


@st.cache_data(show_spinner=False)
def calculate_cached(
    _api: PtxboaAPI,
    scenario: ScenarioType,
    secproc_co2: SecProcCO2Type,
    secproc_water: SecProcH2OType,
    chain: ChainNameType,
    res_gen: ResGenType,
    region: SourceRegionNameType,
    country: TargetCountryNameType,
    transport: TransportType,
    ship_own_fuel: bool,
    output_unit: OutputUnitType,
    user_data: pd.DataFrame | None = None,
    optimize_flh: bool = True,
    use_user_data_for_optimize_flh: bool = False,
    tool_version_color: ToolVersionColorType = "green",
) -> ApiCalculateResult:
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
    res = _api.calculate(
        scenario=scenario,
        secproc_co2=secproc_co2,
        secproc_water=secproc_water,
        chain=chain,
        res_gen=res_gen,
        region=region,
        country=country,
        transport=transport,
        ship_own_fuel=ship_own_fuel,
        output_unit=output_unit,
        user_data=user_data,
        optimize_flh=optimize_flh,
        use_user_data_for_optimize_flh=use_user_data_for_optimize_flh,
        tool_version_color=tool_version_color,
    )

    return res


def calculate_results_list_green(
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

    # check if carbon is needed as input:
    needs_co2 = check_if_input_is_needed(api, flow_code="CO2-G")
    if not needs_co2:
        settings["secproc_co2"] = None

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
        # tool_version_color="green": especially important for "chain"
        parameter_list = api.get_dimension(
            parameter_to_change, tool_version_color="green"
        ).index

    # drop Green Iron if comparing chains (because it is not an energy carrier)
    if parameter_to_change == "chain":
        parameter_list = parameter_list[~parameter_list.str.startswith("Green Iron")]

    res_list = []
    for parameter in parameter_list:
        settings.update({parameter_to_change: parameter})

        if parameter_to_change == "chain":
            needs_co2 = check_if_input_is_needed(
                api,
                flow_code="CO2-G",
                chain=settings["chain"],
                scenario=settings["scenario"],
            )
            # if the current chain does not need CO2, set "secproc_co2" to None
            if needs_co2:
                settings.update({"secproc_co2": st.session_state["secproc_co2"]})
            else:
                settings.update({"secproc_co2": None})

        # for all regions but the selected one, use Wind-PV-hybrid RE source:
        if parameter_to_change == "region":
            if settings["region"] == st.session_state["region"]:
                settings["res_gen"] = st.session_state["res_gen"]
            else:
                settings["res_gen"] = "Wind-PV-Hybrid"

        # consider user data in optimization only for parameter set in session state
        if st.session_state[parameter_to_change] == parameter:
            use_user_data_for_optimize_flh = True
        else:
            use_user_data_for_optimize_flh = False

        # catch all api errors so that the tool is stable
        try:
            res_single = calculate_cached(
                api,
                user_data=(
                    st.session_state["user_changes_df"] if apply_user_data else None
                ),
                optimize_flh=optimize_flh,
                use_user_data_for_optimize_flh=use_user_data_for_optimize_flh,
                **settings,
            ).costs
            res_list.append(res_single)
        except Exception as exc:
            logging.warning(
                "calculate_results_list_green: could not get data for "
                f"{settings=}: {exc}"
            )

    res_details = pd.concat(res_list)

    return aggregate_costs(res_details, parameter_to_change)


def calculate_results_list_blue(
    api: PtxboaAPI,
    parameter_to_change: Literal[
        "region",
        "chain",
        "scenario",
        "WACC",
    ],
    parameter_list: None | list | pd.Series | pd.Index = None,
    override_session_state: dict | None = None,
    apply_user_data: bool = True,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Blue version has fewer settings than green version: no res_gen, no data scenario.

    Fewer dimensions can change.
    Additionally, sensitivities can be calculated by modifying a specific parameter
    value by a range of factors.
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

    # check if carbon is needed as input:
    needs_co2 = check_if_input_is_needed(api, flow_code="CO2-G")
    if not needs_co2:
        settings["secproc_co2"] = None

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
        if parameter_to_change in ["region", "chain", "scenario"]:
            parameter_list = api.get_dimension(
                parameter_to_change, tool_version_color="blue"
            ).index
        elif parameter_to_change in ["WACC"]:
            parameter_list = [0.9, 0.95, 1.0, 1.05, 1.1]
        else:
            raise ValueError(f"invalid {parameter_to_change=}")

    costs_list = []
    emissions_list = []
    emissions_mass_list = []

    if parameter_to_change in ["region", "chain", "scenario"]:
        for change_factor in parameter_list:
            settings.update({parameter_to_change: change_factor})
            if parameter_to_change == "chain":
                needs_co2 = check_if_input_is_needed(
                    api,
                    flow_code="CO2-G",
                    chain=settings["chain"],
                    scenario=settings["scenario"],
                )
                # if the current chain does not need CO2, set "secproc_co2" to None
                if needs_co2:
                    settings.update({"secproc_co2": st.session_state["secproc_co2"]})
                else:
                    settings.update({"secproc_co2": None})

            try:
                res_single = calculate_cached(
                    api,
                    user_data=(
                        st.session_state["user_changes_df"] if apply_user_data else None
                    ),
                    optimize_flh=False,
                    use_user_data_for_optimize_flh=False,
                    tool_version_color="blue",
                    **settings,
                )
                costs_list.append(res_single.costs)
                emissions_list.append(res_single.emissions)
                emissions_mass_list.append(res_single.emission_mass)

            except Exception as exc:
                logging.warning(
                    "calculate_results_list_blue: could not get data for "
                    f"{settings=}: {exc}"
                )

    # sensitivity by changing specific data points by a range of factors
    elif parameter_to_change in ["WACC"]:
        if parameter_to_change == "WACC":
            parameter_code = "WACC"
            process_code = ""
            flow_code = ""
            source_region_code = settings["region"]

        # get input data
        df = api.get_input_data(
            settings["scenario"],
            user_data=(
                st.session_state["user_changes_df"] if apply_user_data else None
            ),
        )
        # get value from input data which is subject to change
        value_df = df.loc[
            (df["parameter_code"] == parameter_code)
            & (df["process_code"] == process_code)
            & (df["flow_code"] == flow_code)
            & (df["source_region_code"] == source_region_code),
            "value",
        ]
        if len(value_df) != 1:
            raise IndexError(f"Not exactly one entry found: {value_df}")
        value = value_df.iloc[0]

        if apply_user_data and st.session_state["user_changes_df"] is not None:
            user_data = st.session_state["user_changes_df"].fillna("")
        else:
            user_data = pd.DataFrame(
                columns=[
                    "source_region_code",
                    "process_code",
                    "parameter_code",
                    "flow_code",
                    "value",
                ]
            ).astype(
                dtype={
                    "source_region_code": "str",
                    "process_code": "str",
                    "parameter_code": "str",
                    "flow_code": "str",
                    "value": "float",
                }
            )

        for change_factor in parameter_list:
            modified = pd.DataFrame(
                data={
                    "source_region_code": source_region_code,
                    "process_code": process_code,
                    "parameter_code": parameter_code,
                    "flow_code": flow_code,
                    "value": value * change_factor,
                },
                index=[0],
            )
            user_data = pd.concat([user_data, modified]).drop_duplicates(
                subset=[
                    "source_region_code",
                    "process_code",
                    "parameter_code",
                    "flow_code",
                ],
                keep="last",
            )
            try:
                res_single = calculate_cached(
                    api,
                    user_data=user_data,
                    optimize_flh=False,
                    use_user_data_for_optimize_flh=False,
                    tool_version_color="blue",
                    **settings,
                )

                def get_label(change_factor, original_value):
                    value_label = f"{(original_value * change_factor):.4f}"
                    if change_factor == 1:
                        return value_label
                    else:
                        pct_change = f"{int(round((change_factor - 1) * 100)):+}%"
                        return f"{value_label} ({pct_change})"

                label = get_label(change_factor, value)
                costs = res_single.costs

                costs_list.append(costs)
                costs[parameter_to_change] = label

                emissions = res_single.emissions
                if emissions is not None:
                    emissions[parameter_to_change] = label
                    emissions_list.append(res_single.emissions)

                emissions_mass = res_single.emission_mass
                if emissions_mass is not None:
                    emissions_mass[parameter_to_change] = label
                    emissions_mass_list.append(res_single.emission_mass)

            except Exception as exc:
                logging.warning(
                    "calculate_results_list_blue: could not get data for "
                    f"{settings=}: {exc}"
                )
    else:
        raise ValueError(f"invalid {parameter_to_change=}")

    costs_details = pd.concat(costs_list)
    emissions_details = pd.concat(emissions_list)
    emissions_mass_details = pd.concat(emissions_mass_list)

    return (
        aggregate_costs(costs_details, parameter_to_change),
        emissions_details,
        emissions_mass_details,
    )


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

    return sort_by_position_in_chain(res)


def aggregate_emissions(
    res_details: pd.DataFrame, index: str, columns: str = "process_type"
) -> pd.DataFrame:
    """Aggregate detailed emissions."""
    res = res_details.pivot_table(
        index=index,
        columns=columns,
        values="values",
        aggfunc="sum",
    )
    # calculate total emissions:
    res["Total"] = res.sum(axis=1)
    return sort_by_position_in_chain(res)


def sort_by_position_in_chain(
    df: pd.DataFrame,
    axis: Literal["columns", "index"] = "columns",
) -> pd.DataFrame:
    """Reorder columns OR index to match the occurrence in a chain."""
    cost_type_order = [
        "Electricity generation",
        "Electrolysis",
        "Electricity and H2 storage",
        "Derivative production",
        "Heat",
        "Water",
        "Carbon",
        "Transportation (Pipeline)",
        "Transportation (Ship)",
        "Final use",
        "CH4",
        "CH4 (direct)",
        "CH4 (indirect)",
        "CO2",
        "CO2 (direct)",
        "CO2 (indirect)",
        "Total",
    ]

    labels = df.columns if axis == "columns" else df.index

    unknown = set(labels) - set(cost_type_order)
    if unknown:
        what = "column(s)" if axis == "columns" else "index value(s)"
        raise ValueError(f"Unrecognized {what}: {', '.join(map(str, unknown))}")

    ordered = [x for x in cost_type_order if x in labels]

    # reindex works for either axis
    return df.reindex(ordered, axis=axis)


def subset_and_pivot_input_data(
    input_data: pd.DataFrame,
    source_region_code: list | None = None,
    parameter_code: list | None = None,
    process_code: list | None = None,
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
        "storage",
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
            df = remove_subregions(api=api, df=df)
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
        "storage",
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
        # remove storage processes
        process_code = [c for c in process_code if "storage" not in c]

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

    if data_type == "storage":
        parameter_code = [
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ]
        process_code = processes.loc[
            processes["process_name"].str.contains("storage"), "process_name"
        ].to_list()

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
        df = remove_subregions(api=api, df=df)
    if scope in ["Argentina", "Morocco", "South Africa"]:
        df = select_subregions(df, scope)

    # transform data to match unit [%] for 'WACC' and 'efficieny'
    if data_type == "WACC":
        df = df * 100

    if "efficiency" in df.columns:
        df["efficiency"] = df["efficiency"] * 100

    return df


def remove_subregions(
    api: PtxboaAPI,
    df: pd.DataFrame,
    keep: str | None = None,
    tool_version_color: ToolVersionColorType | None = None,
):
    """Remove subregions from a dataframe.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    df : pd.DataFrame
        pandas DataFrame with list of regions as index.

    keep : str or None, by default None
        can be used to keep data for a specific subregion

    Returns
    -------
    pandas DataFrame with subregions removed from index.
    """
    # do not show subregions:
    region_list_without_subregions = get_region_list_without_subregions(
        api, keep=keep, tool_version_color=tool_version_color
    )

    # sometimes, not all regions exist
    region_list_without_subregions = [
        r for r in region_list_without_subregions if r in df.index
    ]

    df = df.loc[region_list_without_subregions]

    return df


def get_region_list_without_subregions(
    api: PtxboaAPI,
    keep: str | None,
    tool_version_color: ToolVersionColorType | None = None,
):
    """Get list of regions with subregions removed.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    keep : str or None, by default None
        can be used to keep data for a specific subregion

    Returns
    -------
    list[str]
    """
    region_list_without_subregions = (
        api.get_dimension("region", tool_version_color=tool_version_color)
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )

    if keep is not None:
        region_list_without_subregions.append(keep)

    return sorted(region_list_without_subregions)


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


def config_number_columns(df: pd.DataFrame, **kwargs) -> Dict:
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


@st.cache_data(show_spinner=False)
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
            "process_type": "Processing step",
        }
    new_idx_names = [mapping.get(i, i) for i in df.index.names]
    df.index.names = new_idx_names
    return df


@st.cache_data(show_spinner=False)
def check_if_input_is_needed(
    _api: PtxboaAPI, flow_code: str, chain: str = None, scenario: str = None
) -> bool:
    """Check if a certain input is required by the selected process chain."""
    if chain is None:
        chain = st.session_state["chain"]
    if scenario is None:
        scenario = st.session_state["scenario"]

    # get list of processes in selected chain:
    process_codes = _api.get_dimension("chain").loc[chain][:-1].to_list()
    process_codes = [p for p in process_codes if p != ""]

    # get list of conversion coefficients for these processes:
    df = _api.get_input_data(scenario=scenario, long_names=False)
    flow_codes = df.loc[
        (df["process_code"].isin(process_codes)) & (df["parameter_code"] == "CONV"),
        "flow_code",
    ].to_list()

    return flow_code in flow_codes


def green_costs_over_dimension(
    api, dim, parameter_list=None, override_session_state=None
):
    df = calculate_results_list_green(
        api,
        parameter_to_change=dim,
        parameter_list=parameter_list,
        apply_user_data=True,
        override_session_state=override_session_state,
    )
    if st.session_state["user_changes_df"] is not None:
        not_modified = calculate_results_list_green(
            api,
            parameter_to_change=dim,
            parameter_list=parameter_list,
            apply_user_data=False,
            override_session_state=override_session_state,
        )
    else:
        not_modified = None
    return df, not_modified


@dataclass(slots=True)
class BlueResultOverDimension:
    costs: pd.DataFrame
    emissions: pd.DataFrame
    costs_not_modified: Optional[pd.DataFrame] = None
    emissions_not_modified: Optional[pd.DataFrame] = None


def blue_results_over_dimension(
    api,
    dim: Literal[
        "region",
        "chain",
        "scenario",
        "WACC",
    ],
    emissions_included: Literal["upstream", "final_use", "upstream_and_final_use"],
    parameter_list: None | pd.Series | pd.Index = None,
    override_session_state=None,
):

    def combine_emissions(
        emissions: pd.DataFrame | None,
        emissions_mass: pd.DataFrame | None,
        included: Literal["upstream", "final_use", "upstream_and_final_use"],
    ) -> pd.DataFrame | None:
        if emissions is None and emissions_mass is None:
            return None
        if included == "upstream":
            return emissions
        if included == "final_use":
            return emissions_mass
        if included == "upstream_and_final_use":
            if emissions is None:
                return emissions_mass
            if emissions_mass is None:
                return emissions
            return pd.concat([emissions, emissions_mass])

    costs, emissions, emissions_mass = calculate_results_list_blue(
        api,
        parameter_to_change=dim,
        parameter_list=parameter_list,
        apply_user_data=True,
        override_session_state=override_session_state,
    )

    if st.session_state["user_changes_df"] is not None:
        costs_nm, emissions_nm, emissions_mass_nm = calculate_results_list_blue(
            api,
            parameter_to_change=dim,
            parameter_list=parameter_list,
            apply_user_data=False,
            override_session_state=override_session_state,
        )
    else:
        costs_nm = None
        emissions_nm = None
        emissions_mass_nm = None

    return BlueResultOverDimension(
        costs=costs,
        emissions=combine_emissions(
            emissions, emissions_mass, included=emissions_included
        ),
        costs_not_modified=costs_nm,
        emissions_not_modified=combine_emissions(
            emissions_nm, emissions_mass_nm, included=emissions_included
        ),
    )
