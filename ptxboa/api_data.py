"""Handle data queries for api calculation."""

import logging
from functools import cache
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Tuple, Union, cast

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd

from ptxboa import (
    DEFAULT_DATA_DIR,
    KEY_SEPARATOR,
    PROFILES_DIR,
    STATIC_DATA_DIR,
    logger,
)
from ptxboa.api_optimize import PtxOpt
from ptxboa.static import (
    ChainType,
    DataQueryParameterType,
    DimensionType,
    FlowCodeType,
    OutputUnitValues,
    ParameterCodeType,
    ParameterCodeValues,
    ParameterRangeValues,
    ProcessCodeType,
    ProcessStepType,
)
from ptxboa.static import ProcessStepValues as ProcessStepValuesSorted
from ptxboa.static import (
    ScenarioType,
    ScenarioValues,
    SourceRegionCodeType,
    TargetCountryCodeType,
    ToolVersionColorType,
    TransportType,
    TransportValues,
    YearValues,
)
from ptxboa.static._type_defs import (
    CalculateDataType,
    ChainDef,
    ChainDefStatic,
    ParameterGetter,
    ParameterGetters,
    ProcessDataType,
    ProcessStep,
    PtxCalcResult,
)
from tests.utils import assert_deep_equal, round_nested, sort_nested


def _get_secproc_data(
    secondary_processes: dict,
    pg: "_ParameterGetter",
    has_ccs: bool,
    used_flows_main_export: set,
) -> tuple[dict, set, set]:
    result = {}
    used_flows_secondary: set[FlowCodeType] = set()
    provided_flows_secondary: set[FlowCodeType] = set()
    for flow_code, process_code in secondary_processes.items():
        if not process_code:
            continue
        if flow_code == "CO2-C":
            if not has_ccs:
                continue
        else:
            if flow_code not in used_flows_main_export:
                continue

        pp = pg.get_process_params(process_code)
        pp["process_code"] = process_code

        result[flow_code] = pp
        used_flows_secondary = used_flows_secondary | set(pp["CONV"])
        provided_flows_secondary.add(flow_code)

    return result, used_flows_secondary, provided_flows_secondary


def _assign_key(
    df: pd.DataFrame, key_columns: str | List[str] | Tuple[str]
) -> pd.DataFrame:
    if isinstance(key_columns, str):
        key_columns = [key_columns]
    key_columns = list(key_columns)  # in case we got tuple
    df = df.assign(key=df[key_columns].agg(KEY_SEPARATOR.join, axis=1)).set_index("key")
    if not df.index.unique:
        raise ValueError("duplicate keys in data")
    return df


@cache
def _load_data(
    data_dir: str | Path, name: str, key_columns: str | Tuple[str] | None = None
) -> pd.DataFrame:
    filepath = Path(data_dir) / f"{name}.csv"
    df = pd.read_csv(
        filepath,
        # need to define custom na values due to Alpha2 code of Namibia
        na_values=[
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
        ],
        keep_default_na=False,
    ).drop(columns="key", errors="ignore")
    # numerical columns should never be empty, dimension columns
    # maybe empty and will be filled with ""
    df = df.fillna("")

    # set index
    if key_columns:
        df = _assign_key(df, key_columns)

    return df


def _create_secproc_dimension(dimensions: dict[str, pd.DataFrame], process_class: str):
    return pd.concat(
        [
            dimensions["process"]
            .loc[dimensions["process"]["process_class"] == process_class]
            .copy(),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False)


def _load_dimensions() -> dict[DimensionType, pd.DataFrame]:
    dimensions = {}

    # NOTE / TODO: some are indexed by name, some by code
    dimensions["country"] = _load_data(
        STATIC_DATA_DIR, name="dim_country", key_columns="country_name"
    )
    dimensions["region"] = _load_data(
        STATIC_DATA_DIR, name="dim_region", key_columns="region_name"
    )

    # until this is solved, we load it twice
    dimensions["target_country"] = _load_data(
        STATIC_DATA_DIR, name="dim_country", key_columns="country_code"
    )
    dimensions["source_region"] = _load_data(
        STATIC_DATA_DIR, name="dim_region", key_columns="region_code"
    )

    dimensions["flow"] = _load_data(
        STATIC_DATA_DIR, name="dim_flow", key_columns="flow_code"
    )
    dimensions["parameter"] = _load_data(
        STATIC_DATA_DIR, name="dim_parameter", key_columns="parameter_code"
    )
    dimensions["parameter"] = dimensions["parameter"].assign(
        dimensions=dimensions["parameter"]["dimensions"].apply(
            lambda x: x.split("/") if x else []
        )
    )
    dimensions["process"] = _load_data(
        STATIC_DATA_DIR, name="dim_process", key_columns="process_code"
    )
    dimensions["process"] = dimensions["process"].assign(
        secondary_flows=dimensions["process"]["secondary_flows"].apply(
            lambda x: x.split("/") if x else []
        )
    )
    dimensions["scenario"] = pd.DataFrame(
        [
            {
                "year": year,
                "parameter_range": parameter_range,
                "scenario_name": f"{year} ({parameter_range})",
                "file_name": f"{year}_{parameter_range}",
            }
            for year, parameter_range in product(YearValues, ParameterRangeValues)
        ]
    ).set_index("scenario_name")

    dimensions["secproc_co2"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="PROV_C"
    )
    dimensions["secproc_water"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="PROV_H2O"
    )
    dimensions["secproc_heat"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="PROV_HT"
    )
    dimensions["secproc_el"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="PROV_EL"
    )
    dimensions["secproc_ccs"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="STORC"
    )
    dimensions["secproc_ccs_i"] = _create_secproc_dimension(
        dimensions=dimensions, process_class="STORC"
    )

    dimensions["chain"] = _load_data(
        STATIC_DATA_DIR, name="chains", key_columns="chain"
    )
    dimensions["res_gen"] = (
        dimensions["process"]
        .loc[dimensions["process"]["process_class"] == "RE-GEN"]
        .copy()
        .set_index("process_name", drop=False)
    )
    dimensions["transport"] = pd.DataFrame(
        {"transport_name": TransportValues}
    ).set_index("transport_name", drop=False)
    dimensions["output_unit"] = pd.DataFrame({"unit_name": OutputUnitValues}).set_index(
        "unit_name", drop=False
    )

    # we need a unified list of regions and countries to make code:name
    # translations. Blue countries are also treated as source regions
    # when conversion is happening in demand country.
    dimensions["region_country"] = (
        pd.concat(
            [
                dimensions["region"].rename(
                    columns={
                        "region_code": "region_country_code",
                        "region_name": "region_country_name",
                    }
                ),
                dimensions["country"].rename(
                    columns={
                        "country_code": "region_country_code",
                        "country_name": "region_country_name",
                    }
                ),
            ]
        )
        .loc[
            :,
            [
                "region_country_code",
                "region_country_name",
            ],
        ]
        .drop_duplicates()
    )

    return dimensions


class _ParameterGetter:
    def __init__(
        self,
        data_handler,
        source_region_code,
        target_country_code,
        process_code_res,
        process_code_ely,
        process_code_deriv,
        df_processes,
        df_flows,
        use_user_data: bool = True,
    ):
        self.data_handler = data_handler
        self.source_region_code = source_region_code
        self.target_country_code = target_country_code
        self.process_code_res = process_code_res
        self.process_code_ely = process_code_ely
        self.process_code_deriv = process_code_deriv
        self.df_processes = df_processes
        self.df_flows = df_flows
        self.use_user_data = use_user_data

    def get_parameter_value_w_default(
        self,
        parameter_code: ParameterCodeType,
        process_code: ProcessCodeType | Literal[""] = "",
        flow_code: FlowCodeType | Literal[""] = "",
        default: float | None = None,
    ):
        return self.data_handler._get_parameter_value(
            parameter_code=parameter_code,
            process_code=process_code,
            flow_code=flow_code,
            source_region_code=self.source_region_code,
            target_country_code=self.target_country_code,
            process_code_res=self.process_code_res,
            process_code_ely=self.process_code_ely,
            process_code_deriv=self.process_code_deriv,
            default=default,
            use_user_data=self.use_user_data,
        )

    def get_secondary_flows(self, process_code: ProcessCodeType) -> list[FlowCodeType]:
        flows = self.df_processes.loc[process_code, "secondary_flows"]
        flows = [x for x in flows if x]
        return flows

    def get_secondary_and_main_flows(
        self, process_code: ProcessCodeType
    ) -> list[FlowCodeType]:
        flows = self.get_secondary_flows(process_code)
        proc = self.df_processes.loc[process_code]
        for flow in [proc.main_flow_code_out, proc.main_flow_code_in]:
            if flow and flow not in flows:
                flows.append(flow)
        return list(flows)

    def get_flow_co2_params(
        self, process_code: ProcessCodeType, parameter_code: ParameterCodeType
    ) -> dict:
        result = {}
        flow_codes = self.get_secondary_and_main_flows(process_code)
        for flow_code in flow_codes:
            # new: loss can reduce the effective conversion rate
            value = self.get_parameter_value_w_default(
                parameter_code, flow_code=flow_code, default=0
            )
            if value:
                result[flow_code] = value
        return result

    def get_flow_co2_params_w_process(
        self, process_code: ProcessCodeType, parameter_code: ParameterCodeType
    ) -> dict:
        result = {}
        flow_codes = self.get_secondary_and_main_flows(process_code)
        for flow_code in flow_codes:
            # new: loss can reduce the effective conversion rate
            value = self.get_parameter_value_w_default(
                parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if value:
                result[flow_code] = value
        return result

    def get_flow_loss_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            # new: loss can reduce the effective conversion rate
            loss = self.get_parameter_value_w_default(
                "LOSS", process_code=process_code, flow_code=flow_code, default=0
            )
            if loss:
                result[flow_code] = loss
        return result

    def get_flow_conv_params(
        self,
        process_code: ProcessCodeType,
        flow_loss_params: dict[FlowCodeType, float] | None = None,
    ) -> dict:
        flow_loss_params = flow_loss_params or {}
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            conv = self.get_parameter_value_w_default(
                parameter_code="CONV",
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if conv <= 0:
                # currently negative flows (i.e. additional output)
                # has no value
                continue

            # new: loss can reduce the effective conversion rate
            loss = flow_loss_params.get(flow_code)
            if loss:
                # see https://github.com/agoenergy/ptx-boa/issues/581
                conv = conv * (1 + loss)

            result[flow_code] = conv
        return result

    def get_flow_conv_ot_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        for flow_code in self.get_secondary_flows(process_code):
            conv_ot = self.get_parameter_value_w_default(
                parameter_code="CONV-OT",
                process_code=process_code,
                flow_code=flow_code,
                default=0,
            )
            if conv_ot <= 0:
                continue
            result[flow_code] = conv_ot
        return result

    def get_process_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        result["EFF"] = self.get_parameter_value_w_default(
            "EFF",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("EFF", 0),
        )
        # loss that effects main efficiency: get parameter for
        # main in flow
        main_flow_code_in = self.df_processes.loc[process_code, "main_flow_code_in"]

        # special case NG-PROD#B: has no main_flow_code_in
        if process_code == "NG-PROD#B":
            main_loss_param = self.get_parameter_value_w_default(
                "LOSS",
                process_code=process_code,
                flow_code=self.df_processes.loc[process_code, "main_flow_code_out"],
                default=0,
            )
        else:
            main_loss_param = self.get_parameter_value_w_default(
                "LOSS",
                process_code=process_code,
                flow_code=main_flow_code_in,
                default=0,
            )
        flow_loss_params = self.get_flow_loss_params(process_code)
        if main_loss_param:
            # see https://github.com/agoenergy/ptx-boa/issues/581
            result["EFF"] = result["EFF"] / (1 + main_loss_param)
            result["LOSS"] = main_loss_param

        result["FLH"] = self.get_parameter_value_w_default(
            "FLH",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("FLH", 0),
        )
        result["LIFETIME"] = self.get_parameter_value_w_default(
            "LIFETIME",
            process_code=process_code,
            default=DataHandler.PARAMETER_DEFAULTS.get("LIFETIME", 20),
        )
        result["CAPEX"] = self.get_parameter_value_w_default(
            "CAPEX", process_code=process_code, default=0
        )  # TODO
        result["OPEX-F"] = self.get_parameter_value_w_default(
            "OPEX-F", process_code=process_code, default=0
        )
        result["OPEX-O"] = self.get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )
        result["CONV"] = self.get_flow_conv_params(
            process_code, flow_loss_params=flow_loss_params
        )
        if flow_loss_params:
            result["LOSS_FLOW"] = flow_loss_params

        # additional parameters for co2
        for param in ["CH4SHARE", "EF_M", "EF_E"]:
            value = self.get_flow_co2_params(
                process_code,
                parameter_code=param,  # type: ignore
            )
            if value:
                result[param] = value

        for param in ["CO2CPT-R", "CO2CPT-S", "CBOUND"]:
            value = self.get_flow_co2_params_w_process(
                process_code,
                parameter_code=param,  # type: ignore
            )
            if value:
                result[param] = value

        return result

    def get_transport_process_params(
        self, process_code: ProcessCodeType, dist_transport: float
    ) -> dict:
        result = {}

        loss_t = self.get_parameter_value_w_default(
            "LOSS-T", process_code=process_code, default=0
        )
        result["DIST"] = dist_transport  # TODO: `DIST` not official parameter
        result["EFF"] = 1 - loss_t * dist_transport
        result["OPEX-T"] = self.get_parameter_value_w_default(
            "OPEX-T", process_code=process_code, default=0
        )
        result["OPEX-O"] = self.get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )
        # CONV-OT => CONV? FIXME
        result["CONV-OT"] = self.get_flow_conv_ot_params(process_code)
        result["CONV"] = self.get_flow_conv_params(process_code)
        return result

    def get_flow_params(
        self,
        parameter_code: ParameterCodeType,
        flow_codes: Iterable[FlowCodeType],
        defaults: None | dict = None,
    ):
        defaults = defaults or {}
        result = {}
        for flow_code in flow_codes:
            result[flow_code] = self.get_parameter_value_w_default(
                parameter_code, flow_code=flow_code, default=defaults.get(flow_code)
            )
        return result

    def get_flow_params_for_proc_if_exist(
        self, parameter_code: ParameterCodeType, flow_codes: Iterable[FlowCodeType]
    ):
        result = {}
        for flow_code in flow_codes:
            value = self.get_parameter_value_w_default(
                parameter_code,
                flow_code=flow_code,
                default=0,
            )
            if value:
                result[flow_code] = value
        return result


def _load_scenario_data(data_dir, scenario: str) -> pd.DataFrame:
    scenario_filename = (
        f"{scenario.replace(' ', '_').replace(')', '').replace('(', '')}"
    )
    return _load_data(
        data_dir,
        scenario_filename,
        key_columns=(
            "parameter_code",
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ),
    )


class DataHandler:
    """
    Handler class for parameter retrieval.

    Instances of this class can be used to retrieve data from a single scenario and
    combine it with set user data.
    """

    PARAMETER_DEFAULTS: dict[ParameterCodeType, float] = {
        "EFF": 1,
        "FLH": 7000,
        "LIFETIME": 20,
    }

    dimensions: dict[DimensionType, pd.DataFrame] = _load_dimensions()

    def __init__(
        self,
        scenario: ScenarioType,
        user_data: None | pd.DataFrame = None,
        data_dir: Path = DEFAULT_DATA_DIR,
        cache_dir: Path | None = None,
        tool_version_color: ToolVersionColorType = "green",
    ):
        if scenario not in ScenarioValues:
            raise KeyError(scenario)

        self.scenario = scenario
        self.user_data = user_data
        self.data_dir = data_dir
        self.cache_dir = cache_dir
        self.profiles_path = PROFILES_DIR
        self.tool_version_color = tool_version_color

        self.flh = _load_data(
            self.data_dir,
            name="flh",
            key_columns=(
                "region",
                "process_res",
                "process_ely",
                "process_deriv",
                "process_flh",
            ),
        )

        self._scenario_data = _load_scenario_data(self.data_dir, scenario).copy()

        if user_data is not None:
            self.scenario_data = self._update_scenario_data_with_user_data(
                self._scenario_data, user_data
            )
        else:
            self.scenario_data = self._scenario_data

        self.optimizer = PtxOpt(
            profiles_path=self.profiles_path, cache_dir=self.cache_dir
        )

    @classmethod
    def _map_names_and_codes(
        cls,
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
            if dim in {"region", "country"}:
                # unified mapping for country and region
                mapping = pd.Series(
                    cls.dimensions["region_country"][  # type: ignore
                        f"region_country_{out_type}"
                    ].to_list(),
                    index=cls.dimensions["region_country"][  # type: ignore
                        f"region_country_{in_type}"
                    ],
                )
            else:
                mapping = pd.Series(
                    cls.dimensions[dim][f"{dim}_{out_type}"].to_list(),  # type: ignore
                    index=cls.dimensions[dim][f"{dim}_{in_type}"],  # type: ignore
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

    @classmethod
    def _update_scenario_data_with_user_data(
        cls, scenario_data: pd.DataFrame, user_data: pd.DataFrame
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
        # user data from frontend only has columns
        # "source_region_code", "process_code", "value" and "parameter_code", and
        # "flow_code" we need to replace missing column "target_country_code"
        if "target_country_code" not in user_data.columns:
            user_data = user_data.assign(target_country_code="")
        # user data comes with long names from frontend
        user_data = cls._map_names_and_codes(
            user_data, mapping_direction="name_to_code"
        )
        user_data = _assign_key(
            user_data,
            [
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
            ],
        )
        scenario_data = scenario_data.copy()

        # we only can user DataFrame.update with matching index values
        for key, value in user_data["value"].items():
            scenario_data.at[key, "value"] = value  # type: ignore

        return scenario_data

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
            input_data = self._map_names_and_codes(
                input_data, mapping_direction="code_to_name"
            )
        return input_data

    def _get_parameter_value(
        self,
        parameter_code: ParameterCodeType,
        process_code: ProcessCodeType | None = None,
        flow_code: FlowCodeType | None = None,
        source_region_code: SourceRegionCodeType | None = None,
        target_country_code: TargetCountryCodeType | None = None,
        process_code_res: ProcessCodeType | None = None,
        process_code_ely: ProcessCodeType | None = None,
        process_code_deriv: ProcessCodeType | None = None,
        default: float | None = None,
        use_user_data: bool = True,
    ) -> float:
        """
        Get a parameter value for a process.

        Parameters
        ----------
        parameter_code : ParameterCodeType
            parameter category. Must be one of:
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

        if (
            parameter_code == "FLH"
            and process_code
            not in self.get_dimension("res_gen")["process_code"].to_list()
        ):
            # FLH not changed by user_data
            df = self.flh
            keys = [
                "source_region_code",
                "process_code_res",
                "process_code_ely",
                "process_code_deriv",
                "process_code",
            ]
            required_keys = set(keys)

        else:
            if use_user_data:
                df = self.scenario_data
            else:
                df = self._scenario_data

            keys = [
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
            ]
            required_keys = set(
                self.dimensions["parameter"].at[parameter_code, "dimensions"]  # type: ignore # noqa
            ) | {"parameter_code"}

        def _get_value(
            df: pd.DataFrame, params: dict, keys: list, required_keys: set
        ) -> float | None:
            key = KEY_SEPARATOR.join(
                [params[k] if k in required_keys else "" for k in keys]
            )
            try:
                return df.at[key, "value"]  # type: ignore
            except KeyError:
                return None

        result = _get_value(df, params, keys, required_keys)

        if (
            result is None
            and self.dimensions["parameter"].at[parameter_code, "has_global_default"]
        ):
            # make query with empty "source_region_code"
            result = _get_value(
                df, params, keys, required_keys - {"source_region_code"}
            )

        if result is None and default is not None:
            result = default

        if result is None:
            # FIXME: temporary data
            if self.tool_version_color == "blue":
                if parameter_code == "WACC" and source_region_code == "QAT":
                    result = 0
                else:
                    result = 0
                    logger.warning(
                        f"""did not find a parameter value for:
                        parameter_code={parameter_code},
                        process_code={process_code},
                        flow_code={flow_code},
                        source_region_code={source_region_code},
                        target_country_code={target_country_code},
                        process_code_res={process_code_res},
                        process_code_ely={process_code_ely},
                        process_code_deriv={process_code_deriv},
                        ({self.tool_version_color})
                    """
                    )

            else:
                raise ValueError(
                    f"""did not find a parameter value for:
                    parameter_code={parameter_code},
                    process_code={process_code},
                    flow_code={flow_code},
                    source_region_code={source_region_code},
                    target_country_code={target_country_code},
                    process_code_res={process_code_res},
                    process_code_ely={process_code_ely},
                    process_code_deriv={process_code_deriv}
                    ({self.tool_version_color})
                """
                )
        return result

    @classmethod
    def get_dimension(
        cls,
        dim: DimensionType,
        tool_version_color: ToolVersionColorType | None = None,
    ) -> pd.DataFrame:
        """Delegate get_dimension to underlying data class."""
        df = cls.dimensions[dim]
        # filter data for green / blue tool
        if tool_version_color is not None and dim in {
            "chain",
            "region",
            "country",
            "process",
        }:
            if tool_version_color == "blue":
                df = df.loc[df["is_blue"].astype(bool)]
            elif tool_version_color == "green":
                df = df.loc[df["is_green"].astype(bool)]

        return df

    def get_calculation_data(
        self,
        chain_def: ChainDef,
        optimize_flh: bool,
        use_user_data_for_optimize_flh: bool = False,
    ) -> CalculateDataType:
        """Create data for calculation.

        Parameters
        ----------
        chain_def: ChainDef
        optimize_flh : bool
            _description_
        use_user_data_for_optimize_flh : bool, optional
            _description_, by default True

        Returns
        -------
        CalculateDataType
            _description_
        """
        # get data
        data = self._get_calculation_data(
            chain_def=chain_def,
            use_user_data=True,
        )

        # FIXME: only use this once its tested
        chain_proc = ChainProcess.get_or_create(chain_def)

        data_new = chain_proc.get_calculation_data(
            data_handler=self,
            source_region_code=chain_def.source_region_code,
            optimize_flh=optimize_flh,
            target_country_code=chain_def.target_country_code,
            use_user_data=True,
        )

        if False:  # FIXME
            assert_deep_equal(
                sort_nested(round_nested(data)),
                sort_nested(round_nested(data_new)),
                allow_new_dict_items=True,
            )

        # get optimized FLH?
        if optimize_flh:
            # if we have user data BUT it should NOT be used for optimization
            # get a different dataset for optimization
            if self.user_data is not None and not use_user_data_for_optimize_flh:
                data_opt = self._get_calculation_data(
                    chain_def=chain_def,
                    use_user_data=False,  # THIS IS THE IMPORTANT BIT
                )

                # FIXME: only use this once its tested
                data_opt_new = chain_proc.get_calculation_data(
                    data_handler=self,
                    source_region_code=chain_def.source_region_code,
                    target_country_code=chain_def.target_country_code,
                    optimize_flh=optimize_flh,
                    use_user_data=False,  # THIS IS THE IMPORTANT BIT
                )
                if False:  # FIXME
                    assert_deep_equal(
                        sort_nested(round_nested(data_opt)),
                        sort_nested(round_nested(data_opt_new)),
                        allow_new_dict_items=True,
                    )

            else:
                data_opt = data

            data = self.optimizer.get_calculation_data(data_opt, data)

        return data

    def _get_calculation_data(
        self,
        chain_def: ChainDef,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        """Calculate results."""
        secondary_processes = chain_def.secondary_processes
        chain_name = chain_def.chain_name
        process_code_res = chain_def.process_code_res
        source_region_code = chain_def.source_region_code
        target_country_code = chain_def.target_country_code
        transport = chain_def.transport
        ship_own_fuel = chain_def.ship_own_fuel

        # get process codes for selected chain
        df_processes = self.get_dimension("process")
        df_flows = self.get_dimension("flow")

        chain: dict = dict(self.get_dimension("chain").loc[chain_name])
        process_code_ely = chain["ELY"]
        process_code_deriv = chain["DERIV"]
        chain["RES"] = process_code_res

        pg = _ParameterGetter(
            data_handler=self,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            process_code_res=process_code_res,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
            df_processes=df_processes,
            df_flows=df_flows,
            use_user_data=use_user_data,
        )

        # parameter getter if processes are in import (target) country:
        pg_import = _ParameterGetter(
            data_handler=self,
            source_region_code=target_country_code,  # !!
            target_country_code=target_country_code,
            process_code_res=process_code_res,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
            df_processes=df_processes,
            df_flows=df_flows,
            use_user_data=use_user_data,
        )

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        # get general parameters

        result: CalculateDataType = {
            "flh_opt_process": {},
            "main_export_process_chain": [],
            "transport_process_chain": [],
            "main_import_process_chain": [],
            "secondary_process": {},
            "parameter": {},
            "parameter_i": {},
            "context": {
                "source_region_code": source_region_code,
                "target_country_code": target_country_code,
            },
        }

        result["parameter"]["WACC"] = pg.get_parameter_value_w_default("WACC")
        # default from export country
        result["parameter_i"]["WACC"] = pg_import.get_parameter_value_w_default(
            "WACC", default=result["parameter"]["WACC"]
        )

        # get transport distances and options
        dist_pipeline = pg.get_parameter_value_w_default("DST-S-DP", default=0)
        seashare_pipeline = pg.get_parameter_value_w_default("SEASHARE", default=0)
        existing_pipeline_cap = pg.get_parameter_value_w_default("CAP-T", default=0)
        dist_ship = pg.get_parameter_value_w_default("DST-S-D", default=0)

        transport_distances = self._get_transport_distances(
            source_region_code,
            target_country_code,
            transport,
            ship_own_fuel,
            dist_ship,
            dist_pipeline,
            seashare_pipeline,
            existing_pipeline_cap,
        )

        chain_steps_main_export, chain_steps_transport, chain_steps_main_import = (
            self._filter_chain_processes(chain, transport_distances)
        )

        used_flows_main_chain: set[FlowCodeType] = set()
        used_flows_main_export: set[FlowCodeType] = set()
        has_ccs = False
        for process_step in chain_steps_main_export:
            process_code = chain[process_step]
            pp = pg.get_process_params(process_code)
            pp["step"] = process_step
            pp["process_code"] = process_code
            result["main_export_process_chain"].append(pp)
            used_flows_main_export = used_flows_main_export | set(pp["CONV"])
            proc = self.dimensions["process"].loc[process_code]
            if proc.main_flow_code_in:
                used_flows_main_chain.add(proc.main_flow_code_in)
            if proc.main_flow_code_out:
                used_flows_main_chain.add(proc.main_flow_code_out)

            has_ccs = has_ccs or ("CO2CPT-R" in pp and "CO2CPT-S" in pp)

        _secondary_process, used_flows_secondary, provided_flows_secondary = (
            _get_secproc_data(
                secondary_processes=secondary_processes,
                pg=pg,
                has_ccs=has_ccs,
                used_flows_main_export=used_flows_main_export,
            )
        )
        result["secondary_process"] = _secondary_process

        used_flows_transport: set[FlowCodeType] = set()
        for process_step in chain_steps_transport:
            process_code = chain[process_step]
            if not process_code:
                raise Exception((process_step, chain))
            if process_step in transport_distances:
                dist_transport = transport_distances[process_step]
                pp = pg.get_transport_process_params(process_code, dist_transport)
            else:  # pre/post
                pp = pg.get_process_params(process_code)
            pp["step"] = process_step
            pp["process_code"] = process_code
            result["transport_process_chain"].append(pp)
            used_flows_transport = used_flows_transport | set(pp["CONV"])

            proc = self.dimensions["process"].loc[process_code]
            if proc.main_flow_code_in:
                used_flows_main_chain.add(proc.main_flow_code_in)
            if proc.main_flow_code_out:
                used_flows_main_chain.add(proc.main_flow_code_out)

        used_flows_main_import: set[FlowCodeType] = set()

        has_ccs = False
        for process_step in chain_steps_main_import:
            process_code = chain[process_step]
            if not process_code:
                raise Exception((process_step, chain))
            pp = pg_import.get_process_params(process_code)
            pp["step"] = process_step
            pp["process_code"] = process_code
            result["main_import_process_chain"].append(pp)
            used_flows_main_import = used_flows_main_import | set(pp["CONV"])

            proc = self.dimensions["process"].loc[process_code]
            if proc.main_flow_code_in:
                used_flows_main_chain.add(proc.main_flow_code_in)
            if proc.main_flow_code_out:
                used_flows_main_chain.add(proc.main_flow_code_out)

            has_ccs = has_ccs or ("CO2CPT-R" in pp and "CO2CPT-S" in pp)

        # If RES=Hybrid: we also need PV and Wind-On
        if process_code_res == "RES-HYBR":
            pc: ProcessCodeType
            for pc in ["PV-FIX", "WIND-ON"]:  # type: ignore
                result["flh_opt_process"][pc] = pg.get_process_params(pc)

        used_flows_always_for_opt: set[FlowCodeType] = {
            "H2O-L",
            "CO2-G",
            "N2-G",
            "HEAT",
        }

        used_flows: set[FlowCodeType] = (
            (used_flows_main_export - provided_flows_secondary)
            | used_flows_always_for_opt
            | used_flows_secondary
            | used_flows_transport
            | (used_flows_main_import)
        )
        # FIXME: used_flows_main_import may need to come from different country!!
        result["parameter"]["SPECCOST"] = pg.get_flow_params("SPECCOST", used_flows)

        # default from export country
        result["parameter_i"]["SPECCOST"] = pg_import.get_flow_params(
            "SPECCOST", used_flows, defaults=result["parameter"]["SPECCOST"]
        )

        return result

    @classmethod
    def get_dimensions_parameter_code(
        cls,
        dimension: DimensionType,
        parameter_name: str | None,
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
            "secproc_heat": "process",
            "secproc_el": "process",
            "secproc_ccs": "process",
            "secproc_ccs_i": "process",
            "region": "region",
            "country": "country",
        }
        target_dim_name = dimension_parameter_mapping[dimension]
        df = cls.get_dimension(dimension)

        try:
            return df.loc[
                df[target_dim_name + "_name"] == parameter_name,
                target_dim_name + "_code",
            ].iloc[0]
        except IndexError:
            raise IndexError(
                f"{target_dim_name + '_name'}={parameter_name}, "
                f"{target_dim_name + '_code'}"
            )

    @classmethod
    def _validate_process_chain(
        cls, process_codes: List[ProcessCodeType], final_flow_code: FlowCodeType
    ) -> None:
        df_processes = cls.get_dimension("process")
        flow_code: FlowCodeType | None = None  # initial flow code: can be empty
        for process_code in process_codes:
            process = df_processes.loc[process_code]
            flow_code_in = process["main_flow_code_in"]
            if flow_code and flow_code != flow_code_in:
                raise AssertionError(
                    f"flow_code != flow_code_in in {process_code}: "
                    f"{flow_code} != {flow_code_in}"
                )
            flow_code = process["main_flow_code_out"]  # type: ignore
        if flow_code != final_flow_code:
            raise AssertionError(
                f"flow_code != final_flow_code in {process_code}: "
                f"{flow_code} != {final_flow_code}"
            )

    @classmethod
    def _filter_chain_processes(
        cls, chain: dict, transport_distances: Dict[ProcessStepType, float]
    ) -> tuple[list, list, list]:
        result_main_export = []
        result_main_import = []
        result_transport = []

        for process_step in [
            "RES",
            "NG_PROD",
            "EL_STR",
            "ELY",
            "H2_STR",
            "DERIV",
            "DERIV2",
        ]:
            process_code = chain[process_step]
            if process_code:
                result_main_export.append(process_step)
        is_shipping = transport_distances.get("SHP") or transport_distances.get(
            "SHP_OWN"
        )
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
                if not chain[k]:
                    raise ValueError(f"Missing: {k}")
                result_transport.append(k)

        if is_shipping:
            if chain["POST_SHP"]:  # not all have preprocessing
                # TODO: should maybe be in result_main_import
                result_transport.append("POST_SHP")
        elif is_pipeline:
            if chain["POST_PPL"]:  # not all have preprocessing
                # TODO: should maybe be in result_main_import
                result_transport.append("POST_PPL")

        # optional postprocessing after transport in import country
        for process_step in ["ELY_I", "DERIV_I", "DERIV_I2"]:
            process_code = chain[process_step]
            if process_code:
                result_main_import.append(process_step)

        # CHECK that flow chain is correct
        cls._validate_process_chain(
            [
                chain[p]
                for p in result_main_export + result_transport + result_main_import
            ],
            chain["flow_out"],
        )

        return result_main_export, result_transport, result_main_import

    @staticmethod
    def _get_transport_distances(
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        transport: TransportType,
        ship_own_fuel: bool,
        dist_ship: float,
        dist_pipeline: float,
        seashare_pipeline: float,
        existing_pipeline_cap: float,
    ) -> Dict[ProcessStepType, float]:
        dist_transp = {}
        if source_region_code == target_country_code:
            # no transport (only China)
            pass
        elif dist_pipeline and transport == "Pipeline":
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
                dist_transp["SHP_OWN"] = dist_ship
            else:
                dist_transp["SHP"] = dist_ship

        return dist_transp

    @classmethod
    def get_chain_color(cls, chain: ChainType) -> ToolVersionColorType:
        """Get color from chain."""
        return "blue" if cls.dimensions["chain"].loc[chain, "is_blue"] else "green"

    @classmethod
    def correct_transport(
        cls, transport: TransportType, ship_own_fuel: bool, chain: ChainType
    ) -> tuple[TransportType, bool]:
        """Validate / correct transport."""
        chain_data = cls.dimensions["chain"].loc[chain]
        if transport == "Pipeline" and not chain_data["can_pipeline"]:  # type: ignore
            logger.warning("Cannot use Pipeline - switching to Ship")
            transport = "Ship"

        if ship_own_fuel and (transport != "Ship" or not chain_data["SHP_OWN"]):
            logger.warning("Cannot use ship_own_fuel.")
            ship_own_fuel = False

        return transport, ship_own_fuel


AggregateProcessDataType = tuple[ProcessDataType, dict["Process", ProcessDataType]]


def _plot_get_pos(
    chain_process: "AggregateProcess",
) -> dict["AbstractProcess", tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs[2] = max(xs[0], xs[2])

        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        for process in reversed(list(process_graph.calculate_order)):
            key = process

            # if is_main:
            if process in process_graph.main_processes:
                xs[0] = xs[0] + 2
                x = xs[0]
                y = 0
                if not proc_end_last and process == process_graph.main_processes[0]:
                    y = 0.05  # initial a little closer to secondary
            elif not isinstance(process, MarketProcess):
                #  is secondary
                xs[1] = xs[1] + 1.5
                x = xs[1]
                # non linear disntance for non overlapping arrows
                y = 0.1 + 0.008 * sgn
                sgn = -sgn  # alterante
            else:
                # market
                xs[2] = xs[2] + 1
                x = xs[2]
                y = 0.2

            node_pos[key] = (x, y)

        proc_end_last = process_graph.main_processes[-1]

    return node_pos


class ProcessType:
    def __init__(
        self,
        process_code: ProcessCodeType,
        is_transport: bool,
        is_secondary: bool,
        is_re_generation: bool,
        is_transformation: bool,
        is_storage: bool,
        is_pipeline: bool,
        is_pipeline_retrofitted: bool,
        is_pipeline_sea: bool,
        is_shipping: bool,
        is_shipping_own_fuel: bool,
        main_flow_code_out: FlowCodeType,
        main_flow_code_in: FlowCodeType | None,
        secondary_flows: Iterable[FlowCodeType] | None,
        **_kwargs,
    ):
        self.process_code: ProcessCodeType = process_code
        self.is_transport: bool = is_transport  # includes pre/post transformation
        self.is_secondary: bool = is_secondary
        self.is_transformation: bool = is_transformation
        self.is_storage: bool = is_storage
        self.is_re_generation: bool = is_re_generation
        self.is_pipeline: bool = is_pipeline
        self.is_pipeline_retrofitted: bool = is_pipeline_retrofitted
        self.is_pipeline_sea: bool = is_pipeline_sea
        self.is_shipping: bool = is_shipping
        self.is_shipping_own_fuel: bool = is_shipping_own_fuel
        self.main_flow_code_out: FlowCodeType = main_flow_code_out
        self.main_flow_code_in: FlowCodeType | None = main_flow_code_in
        self.secondary_flow_types: set[FlowCodeType] = (
            set(secondary_flows) if secondary_flows else set()
        )

        # checks
        if self.main_flow_code_in in self.secondary_flow_types:
            logger.error(
                f"{self.process_code}: main_flow_code_in {self.main_flow_code_in} "
                "in secondary_flow_types"
            )
        if self.main_flow_code_out in self.secondary_flow_types:
            logger.error(
                f"{self.process_code}: main_flow_code_out {self.main_flow_code_out} "
                "in secondary_flow_types"
            )
        if self.is_secondary and self.main_flow_code_in:
            logger.warning(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )
        if self.is_initial and self.main_flow_code_in:
            logger.error(
                f"{self.process_code}: should not have "
                f"main flow in: {self.main_flow_code_in}"
            )

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self.is_re_generation or self.process_code == "NG-PROD#B"

    @property
    def is_transport_pre_post(self) -> bool:
        """Process is transport pre/post."""
        return self.is_transport and self.is_transformation and not self.is_storage

    @property
    def is_shipping_or_pipeline(self) -> bool:
        """Without pre/post transformation."""
        return self.is_transport and not self.is_transformation and not self.is_storage

    @property
    def process_class(self) -> type["Process"]:
        """Process class.

        So we can dynamically use subclasses.
        """
        if self.is_initial:
            return InitialProcess
        elif self.is_secondary:
            return SecondaryProcess
        elif self.is_storage:
            return StorageProcess
        elif self.is_transport and not self.is_transformation:
            return TransportProcess
        else:
            return Process

    @property
    def allow_in_export(self) -> bool:
        """Is process allowed in export."""
        return not self.allow_in_transport or self.is_secondary

    @property
    def allow_in_transport(self) -> bool:
        """Is process allowed in transport."""
        return self.is_shipping_or_pipeline

    @property
    def allow_in_import(self) -> bool:
        """Is process allowed in import."""
        # secondary: only allow CCS
        return self.allow_in_export and (
            # CSS is onlyallowed secondary(?) # TODO:generalize?
            not self.is_secondary
            or self.process_code == "CO2-T+S#B"
        )


ProcessTypes: dict[ProcessCodeType, ProcessType] = {
    p["process_code"]: ProcessType(**cast(dict, p))
    for p in DataHandler.get_dimension("process").to_dict(orient="records")
}


class AbstractProcess:
    _parameter_codes_process: list[ParameterCodeType] = []
    _parameter_codes_process_flow: list[ParameterCodeType] = []

    def __init__(
        self,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        self._main_flow_out: float | None = None  # will be set in calculate()
        self._main_flow_in: float | None = None  # will be set in calculate()
        self._secondary_flows_in: dict[FlowCodeType, float] | None = None
        self.parent_process = parent_process
        self.process_step: ProcessStepType | str | None = process_step

    def get_main_flow_out(self) -> float:
        """Value of main out flow."""
        if self._main_flow_out is None:
            raise Exception("Not calculated yet")
        return self._main_flow_out

    def get_main_flow_in(self) -> float:
        """Value of calculated main in flow."""
        if self._main_flow_in is None:
            raise Exception("Not calculated yet, or main_flow_in does not exist")
        return self._main_flow_in

    def get_secondary_flow_in(self, flow_code: FlowCodeType) -> float:
        """Value of calculated secondary in flow for given flow type."""
        if self._secondary_flows_in is None:
            raise Exception(f"Not calculated yet: {self}")
        return self._secondary_flows_in[flow_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return None

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        raise NotImplementedError

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return None

    @property
    def main_flow_code_in_or_out(self) -> FlowCodeType:
        """Main flow code in."""
        return self.main_flow_code_in or self.main_flow_code_out

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return set()

    @property
    def _parameter_flow_types(self) -> set[FlowCodeType]:
        """Flow types for which parameter data should be loaded."""
        result = self.secondary_flow_types
        # also add main flow in (for market/initial proces,
        # those dont exist and we need out)
        result.add(self.main_flow_code_in_or_out)
        # FIXME: for testing compatebility, we also add main_flow out,
        # but can be removed later
        result.add(self.main_flow_code_out)

        return result

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return False

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return False

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return False

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType | None = None,
    ) -> ProcessDataType:
        """Load parameter data for this process."""
        data: ProcessDataType = {}
        # load parameters that are process dependent
        for p in self._parameter_codes_process:
            data[p] = parameter_getters[p](
                process_code=self.process_code,
                flow_code=None,
                source_region_code=source_region_code,
                target_country_code=target_country_code,
            )

        # load parameters that are process and flow dependent
        for p in self._parameter_codes_process_flow:
            data[p] = {
                f: parameter_getters[p](
                    process_code=self.process_code,
                    flow_code=f,
                    source_region_code=source_region_code,
                    target_country_code=target_country_code,
                )
                for f in self._parameter_flow_types
            }

        return data

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        self._main_flow_out = main_flow_out

    def __str__(self):
        s_val = f"={self._main_flow_out:.4f}" if self._main_flow_out else ""
        step = f"{self.process_step}=" if self.process_step else ""
        return f"{self.__class__.__name__}({step}{self.process_code}{s_val})"


class Process(AbstractProcess):
    color = "lightblue"
    _parameter_codes_process = ["LIFETIME", "EFF", "FLH", "CAPEX", "OPEX-F", "OPEX-O"]
    _parameter_codes_process_flow = [
        "CH4SHARE",
        "EF_E",
        "EF_M",
        "CBOUND",
        "CONV-OT",
        "CO2CPT-R",
        "CO2CPT-S",
        "CONV",
        "LOSS",
    ]

    def __init__(
        self,
        process_code: ProcessCodeType,
        process_step: ProcessStepType | str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self._process_type: ProcessType = ProcessTypes[process_code]

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self._process_type.process_code

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._process_type.main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self._process_type.main_flow_code_in

    @property
    def secondary_flow_types(self) -> set[FlowCodeType]:
        """Secondary flow types."""
        return self._process_type.secondary_flow_types

    @property
    def is_initial(self) -> bool:
        """Is this an initial process.

        In green tool, this is a RES generation,
        in blue tool a NG production step.
        """
        return self._process_type.is_initial

    @property
    def is_transport(self) -> bool:
        """Is this a transport process."""
        return self._process_type.is_transport

    @property
    def is_re_generation(self) -> bool:
        """Is this re generation process."""
        return self._process_type.is_re_generation

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType | None = None,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
        )

        # changes

        if "LOSS" in data and "EFF" in data:
            data["LOSS_FLOW"] = data.pop("LOSS")
            if self.main_flow_code_in_or_out in data["LOSS_FLOW"]:  # type: ignore # noqa
                data["LOSS"] = data["LOSS_FLOW"].pop(  # type: ignore
                    self.main_flow_code_in_or_out
                )
            # update EFF and CONV for losses
            # TODO: keep original values for information purposes
            # NOTE: calculation: see https://github.com/agoenergy/ptx-boa/issues/581
            if "LOSS" in data:
                eff_original = data["EFF"]
                data["EFF"] = eff_original / (1 + data["LOSS"])  # type: ignore # noqa

        if "LOSS_FLOW" in data and "CONV" in data:
            # LOSS for CONV (if value exists in both)
            loss_flows = data.get("LOSS_FLOW", {})
            convs = data.get("CONV", {})
            for fc in set(loss_flows) & set(convs):  # type: ignore
                conv_orig = convs[fc]  # type: ignore
                data["CONV"][fc] = conv_orig * (1 + loss_flows[fc])  # type: ignore # noqa

        # FIXME: only for temporary test comparison?
        if (
            any(data.get("CO2CPT-R", {}).values())  # type: ignore
            or any(data.get("CO2CPT-S", {}).values())  # type: ignore
        ) and self.process_code != "CCGT-CC#B":
            logger.warning("TODO: remove dummy CONV for CO2-C")
            data["CONV"]["CO2-C"] = 1  # type: ignore

        return data

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        eff: float = self._parameters.get("EFF")  # type: ignore
        if not eff:
            # logger.warning("EFF = 0") # noqa
            eff = 1

        self._main_flow_in = main_flow_out / eff
        self._secondary_flows_in = {}
        convs = self._parameters.get("CONV", {})  # type: ignore
        for fc in self.secondary_flow_types:
            conv: float = convs.get(fc, 0)  # type: ignore
            value = main_flow_out * conv
            if value < 0:  # ignore (e.g. exothermal heat)
                value = 0
            self._secondary_flows_in[fc] = value


class TransportProcess(Process):
    _parameter_codes_process = ["OPEX-T", "LOSS-T"]
    color = "teal"

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
        )

        # FIXME: we very inefficiently get transport distances every time
        # from parent node

        # FIXME: instead of parent_process(None) -> explicitly link to
        # transport section
        data_all_transports = self.parent_process.get_calculation_data(  # type: ignore
            parameter_getters=parameter_getters,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
        )
        data["DIST"] = data_all_transports["DIST"].get(self.process_step, 0)  # type: ignore # noqa

        logger.warning("Calculate transport EFF")
        data["EFF"] = 1  # FIXME

        return data


class StorageProcess(Process):
    color = "lightsteelblue"


class SecondaryProcess(Process):
    color = "lightgreen"

    @property
    def is_secondary(self) -> bool:
        """Is this a secondary process."""
        return True


class InitialProcess(SecondaryProcess):
    color = "skyblue"


class MarketProcess(AbstractProcess):
    color = "lightgray"
    _parameter_codes_process_flow: list[ParameterCodeType] = ["SPECCOST"]

    def __init__(
        self,
        main_flow_code_out: FlowCodeType,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(parent_process=parent_process)
        self._main_flow_code_out: FlowCodeType = main_flow_code_out

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)
        # TODO

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self._main_flow_code_out

    @property
    def process_code(self) -> ProcessCodeType | None:
        """Process code."""
        return self.main_flow_code_out  # type: ignore


def _get_chain_sections(
    main_process_codes_steps: list["ProcessStep"],
) -> list[tuple[type["ChainSectionProcess"], int, int]]:
    # split and check into export, transport, import
    is_transport = [
        ProcessTypes[p].allow_in_transport for p, _s in main_process_codes_steps
    ]
    # first and last index
    idx_transport_start = is_transport.index(True)
    try:
        idx_transport_end = is_transport.index(False, idx_transport_start)
    except ValueError:  # no import steps
        idx_transport_end = len(is_transport)

    if not (0 < idx_transport_start < idx_transport_end):
        raise Exception("Transport")
    return [  # export,transport,import
        (ChainExportProcess, 0, idx_transport_start),
        (ChainTransportProcess, idx_transport_start, idx_transport_end),
        (ChainImportProcess, idx_transport_end, len(main_process_codes_steps)),
    ]


class AggregateProcess(AbstractProcess):
    def __init__(
        self,
        process_graph: "ProcessGraph",
        process_step: str | None = None,
        parent_process: Union["AbstractProcess", None] = None,
    ):
        super().__init__(process_step=process_step, parent_process=parent_process)
        self.process_graph: "ProcessGraph" = process_graph

    def get_first_main_process_by_step(self, step: ProcessStepType) -> Process:
        """May raise Exception."""
        # TODO: faster if we create lookup dict first
        return next(
            cast(Process, p) for p in self.full_main_chain if p.process_step == step
        )

    @property
    def main_flow_code_out(self) -> FlowCodeType:
        """Main flow code out."""
        return self.process_graph.main_processes[-1].main_flow_code_out

    @property
    def main_flow_code_in(self) -> FlowCodeType | None:
        """Main flow code in."""
        return self.process_graph.main_processes[0].main_flow_code_in

    @property
    def full_main_chain(self) -> list[Process]:
        """List of the entire main chain (including nested aggregated processes)."""
        result: list[Process] = []
        for proc in self.process_graph.main_processes:
            if isinstance(proc, AggregateProcess):
                result += proc.full_main_chain
            else:
                result.append(proc)  # type: ignore - should be Process

        return result

    @property
    def main_processes(self) -> list[AbstractProcess]:
        """List all main proceeses."""
        return self.process_graph.main_processes

    @property
    def secondary_processes(self) -> list[SecondaryProcess]:
        """List of all secondary processes (including nested aggregated processes)."""
        result: list[SecondaryProcess] = []
        for proc in self.process_graph.calculate_order:
            if isinstance(proc, AggregateProcess):
                result += proc.secondary_processes  # recursion
            elif (
                proc.is_secondary
                # NOTE initial is modelled as secondary (because it has no inflow)
                and not proc.is_initial
            ):
                result.append(proc)  # type: ignore should be SecondaryProcess

        return result

    @property
    def secondary_processes_by_flow_code(self) -> dict[FlowCodeType, SecondaryProcess]:
        """List of all secondary processes (including nested aggregated processes)."""
        return {p.main_flow_code_out: p for p in self.secondary_processes}

    @property
    def market_processes_by_flow_code(self) -> dict[FlowCodeType, MarketProcess]:
        """List of all secondary processes (including nested aggregated processes)."""
        return {
            p.main_flow_code_out: p
            for p in self.process_graph.calculate_order
            if isinstance(p, MarketProcess)
        }

    @property
    def main_processes_by_step(self) -> dict[ProcessStepType | str, AbstractProcess]:
        """If exists: get process by step code."""
        return {p.process_step: p for p in self.main_processes if p.process_step}

    def calculate(self, main_flow_out: float):
        """Calculate all process values based on desired output flow."""
        super().calculate(main_flow_out=main_flow_out)

        # in first in reverse order, we use the given main_flow_out
        # for all following, we combine the required flows from all links.
        # if graph iscorrect,these must have been already calculated
        for process in self.process_graph.calculate_order:
            if process == self.process_graph.main_processes[-1]:
                # is last in main chain
                main_flow_out_current = main_flow_out
            else:
                main_flow_out_current = 0  # calculate
                flow_code = process.main_flow_code_out

                for proc_target, in_main in self.process_graph.links_out.get(
                    process, []
                ):
                    logger.debug(f"{process}: Serve {flow_code} to {proc_target}")
                    main_flow_out_current += (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow_code=flow_code)
                    )

                # check
                if not main_flow_out_current:
                    # logger.warning(f"{process}: main_flow_out is 0") # noqa
                    if main_flow_out_current is None:
                        raise ValueError(f"{process}: main_flow_out is None")
            logger.debug(f"Calculate: {process} for {main_flow_out_current}")
            process.calculate(main_flow_out=main_flow_out_current)

            if process == self.process_graph.main_processes[0]:
                self._main_flow_in = process.get_main_flow_in()

    def get_subprocesses_by_class(
        self, class_or_classes: type | tuple[type]
    ) -> list[AbstractProcess]:
        """Get subprocesses byclass."""
        return [
            p
            for p in self.process_graph.calculate_order
            if isinstance(p, class_or_classes)
        ]

    def plot(self, file_basename: str):
        """Create plot and save as png."""
        # Create a directed graph
        G = nx.DiGraph()
        node_labels = {}
        edge_labels = {}
        edge_widths = {}

        proc_end_last = None
        len_main_total = 0
        for ex_tr_imp in self.process_graph.main_processes:
            ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
            # export / tranport / import  subgraph

            process_graph = ex_tr_imp.process_graph

            # add processes as nodes to DiGraph

            for process in reversed(list(process_graph.calculate_order)):
                label = str(process)

                G.add_node(process)
                node_labels[process] = (
                    label.replace("=", "\n")
                    .replace("(", "\n")
                    .replace(")", "\n")
                    .replace(" ", "\n")
                    .strip()
                )

                for proc_target, in_main in process_graph.links_out.get(process, []):
                    flow = process.main_flow_code_out
                    e = (process, proc_target)
                    G.add_edge(*e)
                    try:
                        value = (
                            proc_target.get_main_flow_in()
                            if in_main
                            else proc_target.get_secondary_flow_in(flow)
                        )
                        value_str = f"\n{value:.4f}"
                    except Exception:
                        value_str = ""
                    edge_labels[e] = f"{flow}{value_str}"
                    edge_widths[e] = 2 if in_main else 1

            if proc_end_last:
                # link from previous subpgraph
                proc_start = process_graph.main_processes[0]
                e = (proc_end_last, proc_start)
                G.add_edge(*e)
                edge_labels[e] = proc_end_last.main_flow_code_out
                try:
                    edge_labels[e] += f"\n{proc_start.get_main_flow_in():.4f}"
                except Exception:  # not calculated yet, # noqa: S110
                    pass
                edge_widths[e] = 2

            proc_end_last = process_graph.main_processes[-1]

            len_main_total += len(process_graph.main_processes)

        scale = 3

        # node_pos = nx.circular_layout(G) # noqa
        node_pos = _plot_get_pos(chain_process=self)

        plt.close()
        plt.clf()
        plt.figure(figsize=(len_main_total * scale, 2 * scale))

        # Draw nodes
        nx.draw(
            G,
            node_pos,
            with_labels=False,
            node_color=[cast(Process, k).color for k in G.nodes()],
            width=[edge_widths[k] for k in G.edges()],
            node_size=2000 * scale,
        )

        # Draw node labels
        nx.draw_networkx_labels(
            G, node_pos, labels=node_labels, font_size=6, font_color="black"
        )

        # Draw edge labels
        nx.draw_networkx_edge_labels(
            G,
            node_pos,
            edge_labels=edge_labels,
            font_size=6,
            font_color="black",
            # label_pos=0.5, # noqa
        )

        # Save to PNG
        plt.savefig(f"chain_flowcharts/{file_basename}.png", dpi=150)


class ChainProcess(AggregateProcess):
    _instances: dict[object, "ChainProcess"] = {}

    @classmethod
    def get_or_create(cls, chain_def: ChainDefStatic) -> "ChainProcess":
        """Get or create static instance."""
        key = chain_def.unique_key
        if key not in cls._instances:
            cls._instances[key] = cls._create(chain_def)
        return cls._instances[key]

    def calculate(self, data: CalculateDataType) -> PtxCalcResult:
        """Calcualte results."""
        result: PtxCalcResult = None  # type: ignore
        return result

    @classmethod
    def _create(cls, chain_def: ChainDefStatic) -> "ChainProcess":
        chain_color = DataHandler.get_chain_color(chain_def.chain_name)

        secondary_process_codes = set(chain_def.secondary_processes.values())

        first_process_code: ProcessCodeType
        if chain_color == "blue":
            first_process_code = "NG-PROD#B"
            secondary_process_codes = secondary_process_codes | {
                "HEATPUMP#B",
                "CCGT-CC#B",
                "CO2-T+S#B",
            }  # type: ignore
        else:
            first_process_code = chain_def.process_code_res

        return ChainProcess(
            transport=chain_def.transport,
            ship_own_fuel=chain_def.ship_own_fuel,
            chain=chain_def.chain_name,
            first_process_code=first_process_code,
            secondary_process_codes=secondary_process_codes,  # type: ignore
        )

    def __init__(
        self,
        chain: ChainType,
        first_process_code: ProcessCodeType,
        secondary_process_codes: set[ProcessCodeType],
        transport: TransportType,
        ship_own_fuel: bool,
    ):
        """Create aggregated process for entire chain."""
        chain_data = DataHandler.get_dimension("chain").loc[chain].to_dict()

        main_process_codes_steps: list["ProcessStep"] = [
            (cast(ProcessCodeType, chain_data[step]), cast(ProcessStepType, step))
            for step in ProcessStepValuesSorted
            if chain_data[step]
        ]

        main_process_codes_steps_filtered = _filter_transport_process_codes(
            main_process_codes_steps,
            transport=transport,
            ship_own_fuel=ship_own_fuel,
        )
        # add initial step
        chain_start_with_res = ProcessTypes[first_process_code].is_re_generation
        initial_step = cast(
            ProcessStepType,
            # TODO: maybe from green/blue?
            ("RES" if chain_start_with_res else "NG_PROD"),
        )
        main_process_codes_steps_filtered.insert(0, (first_process_code, initial_step))

        # for FLH lookup we need these process codes
        self._data_lookup_defaults_static: dict[str, ProcessCodeType | None] = {
            "process_res": (first_process_code if chain_start_with_res else None),
            "process_ely": chain_data["ELY"],
            "process_deriv": chain_data["DERIV"],
        }
        self._data_lookup_defaults: dict | None = None  # will be set in init params

        check_use_all_main_process_codes = []

        # FIXME: pre/post shipping processes, remove not required

        main_processes: list[AbstractProcess] = []

        for ChainSectionProcessClass, i, j in _get_chain_sections(
            main_process_codes_steps=main_process_codes_steps_filtered
        ):
            main_process_codes_steps_part: list["ProcessStep"] = (
                main_process_codes_steps_filtered[i:j]
            )

            # if not main_process_codes_steps_part:
            #    continue

            invalid_processes = [
                p
                for p, _s in main_process_codes_steps_part
                if not ChainSectionProcessClass.process_allowed(p)
            ]
            if invalid_processes:
                raise Exception(
                    f"Processes not allowed in {ChainSectionProcessClass.__name__} "
                    f"{main_process_codes_steps_part}: {invalid_processes}"
                )
            secondary_process_codes_part: set[ProcessCodeType] = {
                p
                for p in secondary_process_codes
                if ChainSectionProcessClass.process_allowed(p)
            }

            process = ChainSectionProcessClass(
                main_process_codes_steps=main_process_codes_steps_part,
                secondary_process_codes=secondary_process_codes_part,
                parent_process=self,
            )
            main_processes.append(process)

            check_use_all_main_process_codes = (
                check_use_all_main_process_codes + main_process_codes_steps_part
            )

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes, secondary_processes=[], parent_process=self
        )

        self.section_export: ChainExportProcess = main_processes[0]  # type:ignore
        self.section_transport: ChainTransportProcess = main_processes[1]  # type:ignore
        self.section_import: ChainImportProcess = main_processes[2]  # type:ignore

        super().__init__(
            process_graph=process_graph,
            process_step="CHAIN",
        )

        # check (TODO: can be removed later)
        if not tuple(check_use_all_main_process_codes) == tuple(
            main_process_codes_steps_filtered
        ):
            raise Exception(
                f"{check_use_all_main_process_codes} != "
                f"{main_process_codes_steps_filtered}"
            )
        # check (TODO: can be removed later)
        main_process_codes_ = tuple(p.process_code for p in self.full_main_chain)
        if (
            tuple(p for p, s_ in main_process_codes_steps_filtered)
            != main_process_codes_
        ):
            raise Exception(main_process_codes_)

    def get_calculation_data(
        self,
        data_handler: DataHandler,
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_user_data: bool = True,
        optimize_flh: bool = True,
        todo_transport_re_post_as_transport: bool = True,
    ) -> CalculateDataType:
        """Get calculation data."""
        parameter_getters = _create_parameter_getters(
            data_handler=data_handler, use_user_data=use_user_data
        )

        def _add_step_and_code(
            process: AbstractProcess, data: ProcessDataType
        ) -> ProcessDataType:
            return data | {  # type: ignore
                "process_code": process.process_code,
                "step": process.process_step,
            }

        main_export_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    source_region_code=source_region_code,
                ),
            )
            for p in self.section_export.main_processes
        ]

        main_transport_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    source_region_code=source_region_code,
                    target_country_code=target_country_code,
                ),
            )
            for p in self.section_transport.main_processes
        ]
        main_import_process_chain = [
            _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    source_region_code=target_country_code,
                ),
            )
            for p in self.section_import.main_processes
        ]

        if todo_transport_re_post_as_transport:
            # FIXME: remove after validation:
            # move PRE/POST into transport
            pps_pre = [
                d
                for d in main_export_process_chain
                if d["step"] in {"PRE_PPL", "PRE_SHP"}
            ]
            main_export_process_chain = [
                d
                for d in main_export_process_chain
                if d["step"] not in {"PRE_PPL", "PRE_SHP"}
            ]
            pps_post = [
                d
                for d in main_import_process_chain
                if d["step"] in {"POST_PPL", "POST_SHP"}
            ]
            main_import_process_chain = [
                d
                for d in main_import_process_chain
                if d["step"] not in {"POST_PPL", "POST_SHP"}
            ]
            main_transport_process_chain = (
                pps_pre + main_transport_process_chain + pps_post
            )

        secondary_process = {
            f: _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    source_region_code=source_region_code,
                ),
            )
            for f, p in self.section_export.secondary_processes_by_flow_code.items()
        }
        secondary_process_i = {
            f: _add_step_and_code(
                p,
                p.get_calculation_data(
                    parameter_getters=parameter_getters,
                    source_region_code=target_country_code,
                ),
            )
            for f, p in self.section_import.secondary_processes_by_flow_code.items()
        }

        market_process = {
            f: p.get_calculation_data(
                parameter_getters=parameter_getters,
                source_region_code=source_region_code,
            )
            for f, p in self.section_export.market_processes_by_flow_code.items()
        }
        market_process_i = {
            f: p.get_calculation_data(
                parameter_getters=parameter_getters,
                source_region_code=target_country_code,
            )
            for f, p in self.section_import.market_processes_by_flow_code.items()
        }

        parameter = self.section_export.get_calculation_data(
            parameter_getters=parameter_getters, source_region_code=source_region_code
        ) | {
            "SPECCOST": {f: d["SPECCOST"][f] for f, d in market_process.items()}
        }  # type: ignore # noqa
        parameter_i = self.section_import.get_calculation_data(
            parameter_getters=parameter_getters, source_region_code=target_country_code
        ) | {
            "SPECCOST": {f: d["SPECCOST"][f] for f, d in market_process_i.items()}
        }  # type: ignore # noqa

        flh_opt_process = {}  # noqa
        if optimize_flh:
            # TODO must add flh_opt_process to result
            pass

        return {
            "context": {
                "source_region_code": source_region_code,
                "target_country_code": target_country_code,
            },
            "parameter": parameter,
            "parameter_i": parameter_i,
            "main_export_process_chain": main_export_process_chain,
            "transport_process_chain": main_transport_process_chain,
            "main_import_process_chain": main_import_process_chain,
            "secondary_process": secondary_process,
            "secondary_process_i": secondary_process_i,
        }


class ChainSectionProcess(AggregateProcess):
    _parameter_codes_process = ["WACC"]  # different in export / import

    def __init__(
        self,
        main_process_codes_steps: list["ProcessStep"],
        secondary_process_codes: set[ProcessCodeType],
        parent_process: Union["AbstractProcess", None] = None,
    ):

        main_processes: list[AbstractProcess] = [
            ProcessTypes[pt].process_class(
                process_code=pt, process_step=ps, parent_process=self
            )
            for pt, ps in main_process_codes_steps
        ]
        secondary_processes: list[Process] = [
            ProcessTypes[pt].process_class(process_code=pt, parent_process=self)
            for pt in secondary_process_codes
        ]

        process_graph: ProcessGraph = ProcessGraph(
            main_processes=main_processes,
            secondary_processes=secondary_processes,
            parent_process=self,
        )
        super().__init__(
            process_graph=process_graph,
            parent_process=parent_process,
        )

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return True


class ChainExportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_export


class ChainImportProcess(ChainSectionProcess):
    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_import


class ChainTransportProcess(ChainSectionProcess):
    _parameter_codes_process = [
        "CAP-T",
        "DST-S-D",
        "DST-S-DP",
        "SEASHARE",
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TODO: ugly
        self.transport: TransportType = (
            "Ship"
            if any(
                cast(Process, p)._process_type.is_shipping for p in self.full_main_chain
            )
            else "Pipeline"
        )
        self.ship_own_fuel: bool = any(
            cast(Process, p)._process_type.is_shipping_own_fuel
            for p in self.full_main_chain
        )

    @classmethod
    def process_allowed(cls, process_code: ProcessCodeType) -> bool:
        """Process is allowed as subprocess."""
        return ProcessTypes[process_code].allow_in_transport

    def get_calculation_data(
        self,
        parameter_getters: "ParameterGetters",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
    ) -> ProcessDataType:
        """Get parameter data for this process."""
        data = super().get_calculation_data(
            parameter_getters=parameter_getters,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
        )

        # get transport distances and options
        transport_distances: dict[ProcessStepType, float] = (
            DataHandler._get_transport_distances(
                source_region_code=source_region_code,
                target_country_code=target_country_code,
                transport=self.transport,
                ship_own_fuel=self.ship_own_fuel,
                dist_ship=data["DST-S-D"],  # type: ignore
                dist_pipeline=data["DST-S-DP"],  # type: ignore
                seashare_pipeline=data["SEASHARE"],  # type: ignore
                existing_pipeline_cap=data["CAP-T"],  # type: ignore
            )
        )

        return data | {"DIST": transport_distances}  # type: ignore


def _group_by_flow_type_out(
    process_codes: Iterable[ProcessCodeType],
) -> dict[FlowCodeType, ProcessCodeType]:
    result = {}
    for process_code in process_codes:
        flow_code = ProcessTypes[process_code].main_flow_code_out
        if flow_code in result:
            raise KeyError(f"Multiple items for {flow_code}")
        result[flow_code] = process_code
    return result


class ProcessGraph:
    _KEY_MAIN = "(MAIN)"  # nust not be a flow code

    def __init__(
        self,
        main_processes: list[AbstractProcess],
        secondary_processes: list[Process],
        parent_process: AbstractProcess | None = None,
    ):
        self.main_processes: list[AbstractProcess] = main_processes

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order: Iterable[AbstractProcess] = []
        self.links_out: dict[AbstractProcess, list[tuple[AbstractProcess, bool]]] = {}

        G = nx.DiGraph()
        G.add_nodes_from(main_processes)
        G.add_nodes_from(secondary_processes)

        def add_link_out(
            proc_provider: AbstractProcess,
            proc_recipient: AbstractProcess,
            in_main: bool,
        ):
            # check
            flow_codes_in = (
                {proc_recipient.main_flow_code_in}
                if in_main
                else proc_recipient.secondary_flow_types
            )
            if proc_provider.main_flow_code_out not in flow_codes_in:
                raise Exception(f"Cannot link {proc_provider} => {proc_recipient}")

            if proc_provider not in self.links_out:
                self.links_out[proc_provider] = []
            self.links_out[proc_provider].append((proc_recipient, in_main))
            G.add_edge(proc_provider, proc_recipient)
            logger.debug(
                f"Create link {proc_provider}({proc_provider.main_flow_code_out}) "
                f"{'==>' if in_main else '-->'} {proc_recipient}"
            )

        market_processes: dict[FlowCodeType, MarketProcess] = {}

        def get_or_create_market_process(flow_type: FlowCodeType) -> MarketProcess:
            if flow_type not in market_processes:
                market_processes[flow_type] = MarketProcess(
                    main_flow_code_out=flow_type, parent_process=parent_process
                )
                G.add_node(market_processes[flow_type])
            return market_processes[flow_type]

        # collect all provider of secondary flows (can also come from initial (EL/NG))
        flow_provider_sec_or_initial: dict[FlowCodeType, AbstractProcess] = {}
        first_proc = self.main_processes[0]
        flow_from_initial_proc: FlowCodeType | None = None
        if first_proc.is_initial:
            flow_provider_sec_or_initial[first_proc.main_flow_code_out] = first_proc
            flow_from_initial_proc = first_proc.main_flow_code_out
        for sec_proc in secondary_processes:
            if sec_proc.main_flow_code_out in flow_provider_sec_or_initial:
                logger.warning(f"flow already proveided, skipping {sec_proc}")
                continue
            flow_provider_sec_or_initial[sec_proc.main_flow_code_out] = sec_proc

        # collect required flows
        required_flows_procs: dict[FlowCodeType, list[tuple[AbstractProcess, bool]]] = (
            {}
        )

        def add_required_flows_proc(
            proc: AbstractProcess, flow: FlowCodeType, in_main: bool
        ):
            if flow not in required_flows_procs:
                required_flows_procs[flow] = []
            required_flows_procs[flow].append((proc, in_main))

        for p in main_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
        for p in secondary_processes:
            for f in p.secondary_flow_types:
                add_required_flows_proc(p, f, in_main=False)
            if p.main_flow_code_in:
                # TODO: technically, secondary flows should not have main_flow_code_in
                # but some have them anyways?
                add_required_flows_proc(p, p.main_flow_code_in, in_main=True)

        # match required and provided flows in specific order without creating loops
        # specific order is important so we get a deterministic graph
        def sort_flows_b_priority(
            flow_codes: Iterable[FlowCodeType],
        ) -> Iterable[FlowCodeType]:
            flow_codes_todo = set(flow_codes)
            # FIXME: better way to set priority

            for f in [flow_from_initial_proc, "CO2-C", "EL", "HEAT"]:
                if f in flow_codes_todo:
                    yield f
                    flow_codes_todo.remove(f)

            yield from sorted(flow_codes_todo)

        # link main chain
        for i in range(len(main_processes) - 1):
            add_link_out(main_processes[i], main_processes[i + 1], in_main=True)

        for flow in sort_flows_b_priority(required_flows_procs):
            for proc_target, in_main in required_flows_procs[flow]:
                # try to get from secondary
                prov_sec = flow_provider_sec_or_initial.get(flow)
                if prov_sec:
                    # try to add without loop
                    if nx.has_path(G, proc_target, prov_sec):
                        logger.warning(
                            f"Could not add link {prov_sec} ={flow}=> {proc_target} "
                            "because it would create a loop. fall back on market"
                        )
                        prov_sec = None  # use market
                if not prov_sec:
                    prov_sec = get_or_create_market_process(flow)
                add_link_out(prov_sec, proc_target, in_main=in_main)

        # optional: subgraph to drop unused secondary

        procs_old = set(G.nodes)
        last_proc = self.main_processes[-1]
        G = cast(nx.DiGraph, G.subgraph(nx.ancestors(G, last_proc) | {last_proc}))
        procs_new = set(G.nodes)

        procs_dropped = procs_old - procs_new
        if procs_dropped:
            logger.info("Dropping unused: %s", [str(x) for x in procs_dropped])
            # drop from links_out
            # TODO: maybe use Digraph? - this is very ugly
            for k, vs in self.links_out.items():
                self.links_out[k] = [(p, m) for p, m in vs if p not in procs_dropped]

        # calculate_order: includes main, secondary, tertiary(market) processes
        self.calculate_order = list(reversed(list(nx.topological_sort(G))))

        # check (TODO:can be removed later)
        missing_main = set(self.main_processes) - set(self.calculate_order)
        if missing_main:
            raise Exception(f"missing_main: {missing_main}")


def _filter_transport_process_codes(
    main_process_codes_steps: list["ProcessStep"],
    transport: TransportType,
    ship_own_fuel: bool,
) -> list["ProcessStep"]:
    """If shipping: remove pipeline (and pre/post), and vice versa."""
    drop_steps: set[ProcessStepType | str]

    if transport == "Pipeline":
        drop_steps = {
            "PRE_SHP",
            "POST_SHP",
            "SHP",
            "SHP_OWN",
        }
    elif transport == "Ship":
        drop_steps = {
            "PRE_PPL",
            "PPLS",
            "PPL",
            "PPLX",
            "PPLR",
            "POST_PPL",
        }
        if ship_own_fuel:
            drop_steps = drop_steps | {"SHP"}
        else:
            drop_steps = drop_steps | {"SHP_OWN"}
    else:
        raise NotImplementedError(transport)

    logging.debug(
        "Dropping unused processes: %s",
        [f"{s}={p}" for p, s in main_process_codes_steps if s in drop_steps],
    )
    return [(p, s) for p, s in main_process_codes_steps if s not in drop_steps]


def _create_parameter_getters(
    data_handler: DataHandler, use_user_data: bool
) -> ParameterGetters:

    def _get_df(
        parameter_code: ParameterCodeType, process_code: ProcessCodeType | None
    ):
        if (
            parameter_code == "FLH"
            and process_code
            and not ProcessTypes[process_code].is_re_generation
        ):
            # FLH not changed by user_data
            df = data_handler.flh
        else:
            if use_user_data:
                df = data_handler.scenario_data
            else:
                df = data_handler._scenario_data
        return df

    def _get_parameter_keys(
        parameter_code: ParameterCodeType, use_global_default: bool = False
    ) -> list[tuple[DataQueryParameterType, bool]]:
        if parameter_code == "FLH":
            return [
                (x, True)
                for x in [
                    "source_region_code",  # => region
                    "process_res",
                    "process_ely",
                    "process_deriv",
                    "process_code",  # => process_flh
                ]
            ]  # type: ignore
        else:
            dims = set(
                DataHandler.get_dimension("parameter").at[parameter_code, "dimensions"]  # type: ignore # noqa
            )
            return [
                ("parameter_code", True),
                ("process_code", "process_code" in dims),
                ("flow_code", "flow_code" in dims),
                (
                    "source_region_code",
                    "source_region_code" in dims and not use_global_default,
                ),
                ("target_country_code", "target_country_code" in dims),
            ]

    def make_getter(
        parameter_code: ParameterCodeType, use_global_default: bool
    ) -> ParameterGetter:
        keys = _get_parameter_keys(
            parameter_code, use_global_default=use_global_default
        )

        def _get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **data_lookup_defaults,
        ) -> float | None:
            df = _get_df(parameter_code=parameter_code, process_code=process_code)
            # all available key values
            key_vals = data_lookup_defaults | {
                "parameter_code": parameter_code,
                "process_code": process_code,
                "process_flh": process_code,  # for FLH
                "flow_code": flow_code,
            }
            # join only required key_vals in correct order

            key = ",".join([(key_vals.get(k) or "") if use else "" for k, use in keys])

            try:
                value = cast(float, df.at[key, "value"])
            except Exception:
                value = None

            # FIXME: remove later
            key_debug = ",".join(
                [k + "=" + ((key_vals.get(k) or "") if use else "") for k, use in keys]
            )
            if parameter_code == "FLH":
                key_debug = "parameter_code=FLH," + key_debug
            logger.debug("data lookup: %s => %s", key_debug, value)

            return value

        return _get_value

    def make_getter_2(
        parameter_code: ParameterCodeType,
    ) -> ParameterGetter:
        has_global_default = DataHandler.get_dimension("parameter").at[
            parameter_code, "has_global_default"
        ]

        default_value: float = DataHandler.PARAMETER_DEFAULTS.get(parameter_code, 0)

        _get_value_ = make_getter(
            parameter_code=parameter_code, use_global_default=False
        )
        _get_value_global_default = make_getter(
            parameter_code=parameter_code, use_global_default=True
        )

        def get_value(
            process_code: ProcessCodeType | None = None,
            flow_code: FlowCodeType | None = None,
            **kwargs: str | None,
        ) -> float:
            value = _get_value_(
                process_code=process_code, flow_code=flow_code, **kwargs
            )
            if value is None and has_global_default:
                value = _get_value_global_default(
                    process_code=process_code, flow_code=flow_code, **kwargs
                )
            if value is None:
                # TODO: get complete key
                # logger.warning("No data for %s", key) # noqa
                value = default_value

            return value

        return get_value

    return {
        parameter_code: make_getter_2(parameter_code)  # type: ignore
        for parameter_code in ParameterCodeValues  # type: ignore
    }
