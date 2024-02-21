# -*- coding: utf-8 -*-
"""Handle data queries for api calculation."""

import logging
from functools import cache
from itertools import product
from pathlib import Path
from typing import Dict, List, Literal

import numpy as np
import pandas as pd

from .data.static import DimensionCode  # noqa: will be imported
from .data.static import (
    FlowCode,
    ParameterCode,
    ParameterRangeCode,
    ProcessCode,
    ProcessStep,
    ScenarioCode,
    SourceRegionCode,
    TargetCountryCode,
    YearCode,
)

logger = logging.getLogger(__name__)
DATA_DIR = Path(__file__).parent.resolve() / "data"
DATA_DIR_DIMS = Path(__file__).parent.resolve() / "data"


def _assign_key_index(
    df: pd.DataFrame,
    table_type: Literal["flh", "scenario", "storage_cost_factor"],
) -> pd.DataFrame:
    """
    Assing a unique index to a dataframe containing "index" columns.

    Parameters
    ----------
    df : pd.DataFrame
    table_type : str in {"flh", "scenario", "storage_cost_factor"}

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    ValueError
        if the constructed index is not unique
    """
    keys_in_table = {
        "flh": [
            "region",
            "process_res",
            "process_ely",
            "process_deriv",
            "process_flh",
        ],
        "scenario": [
            "parameter_code",
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ],
        "storage_cost_factor": ["process_res", "process_ely", "process_deriv"],
    }
    key_columns = keys_in_table[table_type]
    df[key_columns] = df[key_columns].astype(str)
    df["key"] = df[key_columns].agg("-".join, axis=1)
    if not df["key"].is_unique:
        raise ValueError(f"duplicate keys in storage {table_type} data.")
    return df.set_index("key")


@cache
def _load_scenario_table(data_dir: str | Path, scenario: ScenarioCode) -> pd.DataFrame:
    df = _load_data(data_dir, scenario).replace(np.nan, "")
    return _assign_key_index(df, table_type="scenario")


@cache
def _load_flh_data(data_dir: str | Path) -> pd.DataFrame:
    df = _load_data(data_dir, name="flh").replace(np.nan, "")
    return _assign_key_index(df, table_type="flh")


@cache
def _load_storage_cost_factor_data(data_dir: str | Path) -> pd.DataFrame:
    df = _load_data(data_dir, name="storage_cost_factor").replace(np.nan, "")
    return _assign_key_index(df, table_type="storage_cost_factor")


def _load_data(data_dir: str | Path, name: str) -> pd.DataFrame:
    filepath = Path(data_dir) / f"{name}.csv"
    df = pd.read_csv(
        filepath,
        # need to define custom na values due to Alpha2 code of Namibia
        na_values={
            "N/A",
            "n/a",
            "NULL",
            "null",
            "NaN",
            "-NaN",
            "nan",
            "-nan",
            "",
            "None",
        },
        keep_default_na=False,
    ).drop(columns="key", errors="ignore")
    # numerical columns should never be empty, dimension columns
    # maybe empty and will be filled with ""
    df = df.fillna("")
    return df


def _get_transport_distances(
    source_region_code: SourceRegionCode,
    target_country_code: TargetCountryCode,
    use_ship: bool,
    ship_own_fuel: bool,
    dist_ship: float,
    dist_pipeline: float,
    seashare_pipeline: float,
    existing_pipeline_cap: float,
) -> Dict[ProcessStep, float]:
    # TODO: new calculation of distances
    dist_transp = {}
    if source_region_code == target_country_code:
        # no transport (only China)
        pass
    elif dist_pipeline and not use_ship:
        # use pipeline if pipeline possible and ship not selected
        if existing_pipeline_cap:
            # use retrofitting
            dist_transp["PPLX"] = dist_pipeline * seashare_pipeline
            dist_transp["PPLR"] = dist_pipeline * (1 - seashare_pipeline)
        else:
            dist_transp["PPLS"] = dist_pipeline * seashare_pipeline
            dist_transp["PPL"] = dist_pipeline * (1 - seashare_pipeline)
    else:
        # use ship
        if ship_own_fuel:
            dist_transp["SHP-OWN"] = dist_ship
        else:
            dist_transp["SHP"] = dist_ship

    return dist_transp


def _filter_chain_processes(
    chain: dict, transport_distances: Dict[ProcessStep, float]
) -> List[ProcessStep]:
    result_main = []
    result_transport = []
    for process_step in ["RES", "ELY", "DERIV"]:
        process_code = chain[process_step]
        if process_code:
            result_main.append(process_step)
    is_shipping = transport_distances.get("SHP") or transport_distances.get("SHP-OWN")
    is_pipeline = (
        transport_distances.get("PPLS")
        or transport_distances.get("PPL")
        or transport_distances.get("PPLX")
        or transport_distances.get("PPLR")
    )
    if is_shipping:
        if chain["PRE_SHP"]:  # not all have preprocessing
            result_transport.append("PRE_SHP")
    elif is_pipeline:
        if chain["PRE_PPL"]:  # not all have preprocessing
            result_transport.append("PRE_PPL")

    for k, v in transport_distances.items():
        if v:
            assert chain[k]
            result_transport.append(k)

    if is_shipping:
        if chain["POST_SHP"]:  # not all have preprocessing
            result_transport.append("POST_SHP")
    elif is_pipeline:
        if chain["POST_PPL"]:  # not all have preprocessing
            result_transport.append("POST_PPL")

    # TODO: CHECK that flow chain is correct

    return result_main, result_transport


def _load_parameter_dims() -> Dict[ParameterCode, dict]:
    # create class instances for parameters
    df_parameters = _load_data(DATA_DIR_DIMS, name="dim_parameter").set_index(
        "parameter_code", drop=False
    )
    assert set(df_parameters.index) == set(ParameterCode.__args__), set(
        ParameterCode.__args__
    ) - set(df_parameters.index)

    PARAMETER_DIMENSIONS = {}
    for parameter_code, specs in df_parameters.iterrows():
        required = [
            y
            for x, y in [
                ("per_flow", "flow_code"),
                ("per_process", "process_code"),
                ("per_region", "source_region_code"),
                ("per_import_country", "target_country_code"),
            ]
            if specs[x]
        ]
        global_default = specs["has_global_default"]

        if global_default:
            assert "source_region_code" in required
        PARAMETER_DIMENSIONS[parameter_code] = {
            "global_default": global_default,
            "required": required,
        }
    return PARAMETER_DIMENSIONS


def _map_names_and_codes(
    scenario_data: pd.DataFrame,
    mapping_direction: Literal["code_to_name", "name_to_code"],
) -> pd.DataFrame:
    """
    Map codes in scenario data to long names and vice versa.

    Mapping is done for data points in the dimensions "parameter", "process",
    "flow", "region", and "country".

    Parameters
    ----------
    scenario_data : pd.DataFrame
    mapping_direction : str in {"code_to_name", "name_to_code"}


    Returns
    -------
    : pd.DataFrame
        Same size as input `scenario_data` but with replaced names/codes
        as a copy of the original data.

    Raises
    ------
    ValueError
        on invalid `mapping_direction` arguments
    """
    if mapping_direction not in ["code_to_name", "name_to_code"]:
        raise ValueError(
            "mapping direction needs to be 'name_to_code' or 'code_to_name'"
        )
    in_type = mapping_direction.split("_")[0]
    out_type = mapping_direction.split("_")[-1]

    for dim in ["parameter", "process", "flow", "region", "country"]:
        mapping = pd.Series(
            dimensions[dim][f"{dim}_{out_type}"].to_list(),
            index=dimensions[dim][f"{dim}_{in_type}"],
        )
        if dim not in ["region", "country"]:
            column_name = f"{dim}_code"
        elif dim == "region":
            column_name = "source_region_code"
        elif dim == "country":
            column_name = "target_country_code"
        scenario_data[column_name] = scenario_data[column_name].map(
            mapping, na_action="ignore"
        )
    scenario_data = scenario_data.replace(np.nan, "")
    return scenario_data


def _update_scenario_data_with_user_data(
    scenario_data: pd.DataFrame, user_data: pd.DataFrame
):
    """
    Update scenario_data with custom user_data.

    Parameters
    ----------
    scenario_data : pd.DataFrame
        the (unmodfied) scenario data
    user_data : pd.DataFrame
        user data containing only rows of scenario_data that have been modified.
        The ids in the received user data from frontend are long names and need to
        be mapped to codes first.
    """
    user_data = user_data.copy().fillna("")
    scenario_data = scenario_data.copy()
    # user data from frontend only has columns
    # "source_region_code", "process_code", "value" and "parameter_code", and
    # "flow_code" we need to replace missing column "target_country_code"
    user_data["target_country_code"] = ""

    # user data comes with long names from frontend
    user_data = _map_names_and_codes(user_data, mapping_direction="name_to_code")

    # we only can user DataFrame.update with matching index values
    # but we do not want tu use "key"
    for row in user_data.itertuples():
        selector = (
            (scenario_data["parameter_code"] == row.parameter_code)
            & (scenario_data["process_code"] == row.process_code)
            & (scenario_data["flow_code"] == row.flow_code)
            & (scenario_data["source_region_code"] == row.source_region_code)
            & (scenario_data["target_country_code"] == row.target_country_code)
        )
        if len(scenario_data.loc[selector]) == 0:
            raise ValueError(f"could not replace user_parameterin scenario_data\n{row}")
        scenario_data.loc[selector, "value"] = row.value
    return scenario_data


parameters = _load_parameter_dims()
chains = _load_data(DATA_DIR_DIMS, name="chains").set_index("chain").replace(np.nan, "")
dimensions = {
    dim: _load_data(DATA_DIR_DIMS, name=f"dim_{dim}")
    for dim in ["country", "flow", "parameter", "process", "region"]
}
dimensions2 = {
    "scenario": pd.DataFrame(
        [
            {
                "year": year,
                "parameter_range": parameter_range,
                "scenario_name": f"{year} ({parameter_range})",
                "file_name": f"{year}_{parameter_range}",
            }
            for year, parameter_range in product(
                YearCode.__args__, ParameterRangeCode.__args__
            )
        ]
    ).set_index("scenario_name"),
    "secproc_co2": pd.concat(
        [
            dimensions["process"]
            .loc[dimensions["process"]["process_class"] == "PROV_C"]
            .copy(),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False),
    "secproc_water": pd.concat(
        [
            (
                dimensions["process"]
                .loc[dimensions["process"]["process_class"] == "PROV_H2O"]
                .copy()
            ),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False),
    "chain": chains.copy(),
    "res_gen": (
        dimensions["process"]
        .loc[dimensions["process"]["process_class"] == "RE-GEN"]
        .copy()
        .set_index("process_name", drop=False)
    ),
    "region": dimensions["region"].set_index("region_name", drop=False),
    "country": (
        dimensions["country"]
        .loc[dimensions["country"]["is_import"]]
        .set_index("country_name", drop=False)
    ),
    "transport": pd.DataFrame(
        [{"transport_name": "Ship"}, {"transport_name": "Pipeline"}]
    ).set_index("transport_name", drop=False),
    "output_unit": pd.DataFrame(
        [{"unit_name": "USD/MWh"}, {"unit_name": "USD/t"}]
    ).set_index("unit_name", drop=False),
    "process": dimensions["process"].set_index("process_code", drop=False),
    "flow": dimensions["flow"].set_index("flow_code", drop=False),
    "parameter": dimensions["parameter"].set_index("parameter_code", drop=False),
}


class DataHandler:
    """
    Handler class for parameter retrieval.

    Instances of this class can be used to retrieve data from a single scenario and
    combine it with set user data.
    """

    def __init__(
        self,
        scenario: ScenarioCode,
        user_data: None | pd.DataFrame = None,
        data_dir: str = None,
    ):

        assert scenario in ScenarioCode.__args__

        self.scenario = scenario
        self.user_data = user_data
        self.data_dir = data_dir or DATA_DIR

        self.flh = _load_flh_data(self.data_dir)
        self.storage_cost_factor = _load_storage_cost_factor_data(self.data_dir)

        self.scenario_data = _load_scenario_table(
            self.data_dir,
            f"{scenario.replace(' ', '_').replace(')', '').replace('(', '')}",
        ).copy()

        if user_data is not None:
            self.scenario_data = _update_scenario_data_with_user_data(
                self.scenario_data, user_data
            )

    def get_input_data(self, long_names: bool) -> pd.DataFrame:
        """Return scenario data.

        If user data is defined, specified values will be replaced with those.

        Parameters
        ----------
        long_names : bool, optional
            if True, will replace the codes used internally with long names that are
            used in the frontend.

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        input_data = self.scenario_data
        if long_names:
            input_data = _map_names_and_codes(
                input_data, mapping_direction="code_to_name"
            )
        return input_data

    def _get_parameter_value(
        self,
        parameter_code: ParameterCode,
        process_code: ProcessCode = None,
        flow_code: FlowCode = None,
        source_region_code: SourceRegionCode = None,
        target_country_code: TargetCountryCode = None,
        process_code_res: ProcessCode = None,
        process_code_ely: ProcessCode = None,
        process_code_deriv: ProcessCode = None,
        default: float = None,
    ) -> float:
        """
        Get a parameter value for a process.

        Parameters
        ----------
        parameter_code : ParameterCode
            parameter category. Must be one of:
                - 'CALOR',
                - 'CAPEX'
                - 'CAP-T'
                - 'CONV'
                - 'DST-S-D'
                - 'DST-S-DP'
                - 'EFF'
                - 'FLH'
                - 'LIFETIME'
                - 'LOSS-T'
                - 'OPEX-F'
                - 'OPEX-T'
                - 'RE-POT'
                - 'SEASHARE'
                - 'SPECCOST'
                - 'WACC'
        process_code : str, optional
            Code for the process, by default None. Must be set for the following
            parameters:
                - CAPEX
                - CONV
                - EFF
                - FLH
                - LIFETIME
                - LOSS-T
                - OPEX-F
                - OPEX-T
                - RE-POT
                - WACC
        flow_code : str, optional
            Code for the flow, by default None. Must be set for the following
            parameters:
                - CALOR
                - CONV
                - SPECCOST
        source_region_code : str, optional
            Code for the source region, by default None. Must be set for the
            following parameters:
                - CAPEX
                - CAP-T
                - DST-S-D
                - DST-S-DP
                - FLH
                - OPEX-F
                - RE-POT
                - SEASHARE
                - SPECCOST
                - WACC
        target_country_code : str, optional
            Code for the target country, by default None. Must be set for the
            following parameters:
                - CAP-T
                - DST-S-D
                - DST-S-DP
                - SEASHARE
        process_code_res : str, optional
            Code for the process_code_res, by default None. Must be set for the
            following parameters:
                - FLH
        process_code_ely : str, optional
            Code for the process_code_ely, by default None. Must be set for the
            following parameters:
                - FLH
        process_code_deriv : str, optional
            Code for the process_code_deriv, by default None. Must be set for the
            following parameters:
                - FLH

        default : float, optional
            if no data is found, this value is returned.
            if no data is found and default is not specified, a ValueError is raised.

        Returns
        -------
        float
            the parameter value

        Raises
        ------
        ValueError
            if multiple values are found for a parameter combination.
        ValueError
            if no value is found for a parameter combination and no default is given.
        """
        # convert missing codes tom empty strings
        # for data matching
        params = {
            "parameter_code": parameter_code,
            "process_code": process_code or "",
            "flow_code": flow_code or "",
            "source_region_code": source_region_code or "",
            "target_country_code": target_country_code or "",
            "process_code_res": process_code_res or "",
            "process_code_ely": process_code_ely or "",
            "process_code_deriv": process_code_deriv or "",
        }

        self._check_required_parameter_value_kwargs(
            parameter_code,
            process_code=process_code,
            flow_code=flow_code,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            process_code_res=process_code_res,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
        )

        if (
            parameter_code == "FLH"
            and process_code
            not in self.get_dimension("res_gen")["process_code"].to_list()
        ):
            # FLH not changed by user_data
            df = self.flh
            key = "-".join(
                [
                    params[k]
                    for k in [
                        "source_region_code",
                        "process_code_res",
                        "process_code_ely",
                        "process_code_deriv",
                        "process_code",
                    ]
                ]
            )
        elif parameter_code == "STR-CF":
            # Storage cost factor not changed by user (and currently in separate file)
            df = self.storage_cost_factor
            key = "-".join(
                [
                    params[k]
                    for k in [
                        "process_code_res",
                        "process_code_ely",
                        "process_code_deriv",
                    ]
                ]
            )
        else:
            df = self.scenario_data
            key = self._construct_key_in_scenario_data(params)

        try:
            row = df.at[key, "value"]
            empty_result = False
        except KeyError:
            empty_result = True
        if empty_result and parameters[parameter_code]["global_default"]:
            # make query with empty "source_region_code"
            logger.debug(
                f"searching global default, did not find entry for key '{key}'"
            )
            params["source_region_code"] = ""
            params["target_country_code"] = ""
            key = self._construct_key_in_scenario_data(params)
            try:
                row = df.at[key, "value"]
                empty_result = False
            except KeyError:
                empty_result = True

        if empty_result:
            if default is not None:
                return default
            raise ValueError(
                f"""did not find a parameter value for key '{key}':
                parameter_code={parameter_code},
                process_code={process_code},
                flow_code={flow_code},
                source_region_code={source_region_code},
                target_country_code={target_country_code},
                process_code_res={process_code_res},
                process_code_ely={process_code_ely},
                process_code_deriv={process_code_deriv},
            """
            )
        return row

    def _construct_key_in_scenario_data(
        self,
        params: dict,
    ) -> pd.Series:
        """
        Create a boolean index object which can be used to filter df.

        Parameters
        ----------
        params : dict
            dictionary which needs to contain the following keys:
            ["parameter_code", "process_code", "flow_code", "source_region_code",
            "target_country_code"]
        """
        selector = params["parameter_code"]
        for k in [
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ]:
            if k in parameters[params["parameter_code"]]["required"]:
                selector += f"-{params[k]}"
            else:
                selector += "-"
        return selector

    def _check_required_parameter_value_kwargs(
        self,
        parameter_code: ParameterCode,
        **kwargs,
    ):
        """
        Check parameters passed to `self.get_parameter_value()`.

        Check that required parameter dimensions are not None and that
        unused dimensions are None.

        Parameters
        ----------
        parameter_code : str
        kwargs :
            keyword arguments passed to `self.get_parameter_value()`
        """
        required_param_names = parameters[parameter_code]["required"]

        for p in required_param_names:
            required_value = kwargs.pop(p)
            if not required_value:
                raise ValueError(
                    f"'{parameter_code}': the following parameters must be "
                    f"defined\n{required_param_names}\n"
                    f"Got: {kwargs}"
                )

    @staticmethod
    def get_dimension(dim: str) -> pd.DataFrame:
        """Delegate get_dimension to underlying data class."""
        return dimensions2[dim]

    def get_calculation_data(
        self,
        secondary_processes: Dict[FlowCode, ProcessCode],
        chain: dict,
        process_code_res: ProcessCode,
        process_code_ely: ProcessCode,
        process_code_deriv: ProcessCode,
        source_region_code: SourceRegionCode,
        target_country_code: TargetCountryCode,
        use_ship: bool,
        ship_own_fuel: bool,
    ) -> pd.DataFrame:
        """Calculate results."""
        # get process codes for selected chain
        df_processes = self.get_dimension("process")
        df_flows = self.get_dimension("flow")

        def get_parameter_value_w_default(
            parameter_code, process_code="", flow_code="", default=None
        ):
            return self._get_parameter_value(
                parameter_code=parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                source_region_code=source_region_code,
                target_country_code=target_country_code,
                process_code_res=process_code_res,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
                default=default,
            )

        def flow_conv_params(process_code):
            result = {}
            flows = df_processes.loc[process_code, "secondary_flows"].split("/")
            flows = [x.strip() for x in flows if x.strip()]
            for flow_code in flows:
                result[flow_code] = get_parameter_value_w_default(
                    parameter_code="CONV",
                    process_code=process_code,
                    flow_code=flow_code,
                    default=0,
                )
            return result

        def get_process_params(process_code):
            result = {}
            result["EFF"] = get_parameter_value_w_default(
                "EFF", process_code=process_code, default=1
            )
            result["FLH"] = get_parameter_value_w_default(
                "FLH", process_code=process_code, default=7000  # TODO: default?
            )
            result["LIFETIME"] = get_parameter_value_w_default(
                "LIFETIME", process_code=process_code, default=20  # TODO: default?
            )
            result["CAPEX"] = get_parameter_value_w_default(
                "CAPEX", process_code=process_code, default=0
            )  # TODO
            result["OPEX-F"] = get_parameter_value_w_default(
                "OPEX-F", process_code=process_code, default=0
            )
            result["OPEX-O"] = get_parameter_value_w_default(
                "OPEX-O", process_code=process_code, default=0
            )
            result["CONV"] = flow_conv_params(process_code)

        def get_transport_process_params(process_code, dist_transport):
            result = {}
            # TODO: also save in results
            loss_t = get_parameter_value_w_default(
                "LOSS-T", process_code=process_code, default=0
            )
            result["EFF"] = 1 - loss_t * dist_transport
            result["OPEX-T"] = get_parameter_value_w_default(
                "OPEX-T", process_code=process_code, default=0
            )
            result["OPEX-O"] = get_parameter_value_w_default(
                "OPEX-O", process_code=process_code, default=0
            )
            result["CONV"] = flow_conv_params(process_code)
            return result

        def get_flow_params():
            # TODO: only get used flows?
            secondary_flows = list(
                df_flows.loc[df_flows["secondary_flow"], "flow_code"]
            )
            result = {}
            for flow_code in secondary_flows:
                result[flow_code] = get_parameter_value_w_default(
                    "SPECCOST", flow_code=flow_code
                )
            return result

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        # get general parameters

        result = {
            "main_process_chain": [],
            "transport_process_chain": [],
            "secondary_process": {},
            "parameter": {},
        }

        result["parameter"]["WACC"] = get_parameter_value_w_default("WACC")
        result["parameter"]["STR-CF"] = get_parameter_value_w_default("STR-CF")
        result["parameter"]["CALOR"] = get_parameter_value_w_default(
            parameter_code="CALOR", flow_code=chain["FLOW_OUT"]
        )
        result["parameter"]["SPECCOST"] = get_flow_params()

        # get transport distances and options
        # TODO? add these also to data
        dist_pipeline = get_parameter_value_w_default("DST-S-DP", default=0)
        seashare_pipeline = get_parameter_value_w_default("SEASHARE", default=0)
        existing_pipeline_cap = get_parameter_value_w_default("CAP-T", default=0)
        dist_ship = get_parameter_value_w_default("DST-S-D", default=0)

        if not use_ship and not chain["CAN_PIPELINE"]:
            logging.warning("Must use ship")
            use_ship = True

        transport_distances = _get_transport_distances(
            source_region_code,
            target_country_code,
            use_ship,
            ship_own_fuel,
            dist_ship,
            dist_pipeline,
            seashare_pipeline,
            existing_pipeline_cap,
        )

        chain["RES"] = process_code_res

        chain_steps_main, chain_steps_transport = _filter_chain_processes(
            chain, transport_distances
        )

        for process_step in chain_steps_main:
            process_code = chain[process_step]
            res = get_process_params(process_code)
            result["main_process_chain"].append(res)

        for flow_code, process_code in secondary_processes.items():
            if not process_code:
                continue
            res = get_process_params(process_code)
            result["secondary_process"][flow_code] = res

        for process_step in chain_steps_transport:
            process_code = chain[process_step]
            if not process_code:
                raise Exception((process_step, chain))
            if process_step in transport_distances:
                dist_transport = transport_distances[process_step]
                res = get_transport_process_params(process_code, dist_transport)
            else:  # pre/post
                res = get_process_params(process_code)
            result["transport_process_chain"].append(res)

        return result

    @classmethod
    def get_dimensions_parameter_code(
        cls,
        dimension: Literal[
            "res_gen", "secproc_co2", "secproc_water", "region", "country"
        ],
        parameter_name: str,
    ) -> str:
        """
        Get the internal code for a paremeter within a certain dimension.

        Used to translate long name parameters from frontend to codes.

        Parameters
        ----------
        dimension : str
        parameter_name : str

        Returns
        -------
        str
        """
        if not parameter_name or parameter_name == "Specific costs":
            return ""

        # mapping of different parameter dimension names depending on "dimension"
        dimension_parameter_mapping = {
            "res_gen": "process",
            "secproc_co2": "process",
            "secproc_water": "process",
            "region": "region",
            "country": "country",
        }
        target_dim_name = dimension_parameter_mapping.get(dimension)
        df = cls.get_dimension(dimension)
        return df.loc[
            df[target_dim_name + "_name"] == parameter_name, target_dim_name + "_code"
        ].iloc[0]
