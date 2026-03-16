"""Handle data queries for api calculation."""

from functools import cache
from itertools import product
from pathlib import Path
from typing import Dict, Iterable, List, Literal, Tuple

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
    ChainNameType,
    DimensionType,
    FlowCodeType,
    OutputUnitValues,
    ParameterCodeType,
    ParameterRangeValues,
    ProcessCodeResType,
    ProcessCodeType,
    ProcessStepType,
    ScenarioType,
    ScenarioValues,
    SourceRegionCodeType,
    TargetCountryCodeType,
    ToolVersionColorType,
    TransportValues,
    YearValues,
)
from ptxboa.static._types import CalculateDataType


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
    dimensions["secproc_co2"] = pd.concat(
        [
            dimensions["process"]
            .loc[dimensions["process"]["process_class"] == "PROV_C"]
            .copy(),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False)
    dimensions["secproc_water"] = pd.concat(
        [
            (
                dimensions["process"]
                .loc[dimensions["process"]["process_class"] == "PROV_H2O"]
                .copy()
            ),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False)
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

    def get_process_params(self, process_code: ProcessCodeType) -> dict:
        result = {}
        result["EFF"] = self.get_parameter_value_w_default(
            "EFF", process_code=process_code, default=1
        )
        # loss that effects main efficiency: get parameter for
        # main in flow
        main_flow_code_in = self.df_processes.loc[process_code, "main_flow_code_in"]
        main_loss_param = self.get_parameter_value_w_default(
            "LOSS", process_code=process_code, flow_code=main_flow_code_in, default=0
        )
        flow_loss_params = self.get_flow_loss_params(process_code)
        if main_loss_param:
            # see https://github.com/agoenergy/ptx-boa/issues/581
            result["EFF"] = result["EFF"] / (1 + main_loss_param)
            result["LOSS"] = main_loss_param

        result["FLH"] = self.get_parameter_value_w_default(
            "FLH",
            process_code=process_code,
            default=7000,  # TODO: default?
        )
        result["LIFETIME"] = self.get_parameter_value_w_default(
            "LIFETIME",
            process_code=process_code,
            default=20,  # TODO: default?
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
        # TODO: country dependent?

        for param in ["CO2CPT-R", "CO2CPT-S"]:
            value = self.get_parameter_value_w_default(
                parameter_code=param,  # type:ignore
                process_code=process_code,
                default=0,
            )
            if value:
                result[param] = value

        for param in ["CO2BOUND", "CH4SHARE", "EF_M", "EF_E"]:
            value = self.get_flow_co2_params(
                process_code, parameter_code=param
            )  # type:ignore
            if value:
                result[param] = value

        return result

    def get_transport_process_params(
        self, process_code: ProcessCodeType, dist_transport: float
    ) -> dict:
        result = {}
        # TODO: also save in results
        loss_t = self.get_parameter_value_w_default(
            "LOSS-T", process_code=process_code, default=0
        )
        result["DIST"] = dist_transport  # TODO: `DIST` not oficcial parameter
        result["EFF"] = 1 - loss_t * dist_transport
        result["OPEX-T"] = self.get_parameter_value_w_default(
            "OPEX-T", process_code=process_code, default=0
        )
        result["OPEX-O"] = self.get_parameter_value_w_default(
            "OPEX-O", process_code=process_code, default=0
        )
        result["CONV"] = self.get_flow_conv_params(process_code)
        return result

    def get_flow_params(
        self, parameter_code: ParameterCodeType, flow_codes: Iterable[FlowCodeType]
    ):
        result = {}
        for flow_code in flow_codes:
            result[flow_code] = self.get_parameter_value_w_default(
                parameter_code,
                flow_code=flow_code,
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


class DataHandler:
    """
    Handler class for parameter retrieval.

    Instances of this class can be used to retrieve data from a single scenario and
    combine it with set user data.
    """

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

        scenario_filename = (
            f"{scenario.replace(' ', '_').replace(')', '').replace('(', '')}"
        )
        self._scenario_data = _load_data(
            self.data_dir,
            scenario_filename,
            key_columns=(
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
            ),
        ).copy()

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
                    cls.dimensions["region_country"][  # type:ignore
                        f"region_country_{out_type}"
                    ].to_list(),
                    index=cls.dimensions["region_country"][
                        f"region_country_{in_type}"
                    ],  # type:ignore
                )
            else:
                mapping = pd.Series(
                    cls.dimensions[dim][f"{dim}_{out_type}"].to_list(),  # type:ignore
                    index=cls.dimensions[dim][f"{dim}_{in_type}"],  # type:ignore
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
            scenario_data.at[key, "value"] = value  # type:ignore

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
        # FIXME: replace with a cleaner, faster,class based lookup per parameter

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
                self.dimensions["parameter"].at[
                    parameter_code, "dimensions"
                ]  # type:ignore
            ) | {"parameter_code"}

        def _get_value(
            df: pd.DataFrame, params: dict, keys: list, required_keys: set
        ) -> float | None:
            key = KEY_SEPARATOR.join(
                [params[k] if k in required_keys else "" for k in keys]
            )
            try:
                return df.at[key, "value"]  # type:ignore
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
                if parameter_code == "CALOR" and flow_code == "STL-S":
                    result = 1
                elif parameter_code == "WACC" and source_region_code == "QAT":
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
        secondary_processes: Dict[FlowCodeType, ProcessCodeType],
        chain_name: ChainNameType,
        process_code_res: ProcessCodeResType,
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_ship: bool,
        ship_own_fuel: bool,
        optimize_flh: bool,
        use_user_data_for_optimize_flh: bool = False,
    ) -> CalculateDataType:
        """Create data for calculation.

        Parameters
        ----------
        secondary_processes : Dict[FlowCodeType, ProcessCodeType]
            _description_
        chain_name : ChainNameType
            _description_
        process_code_res : ProcessCodeResType
            _description_
        source_region_code : SourceRegionCodeType
            _description_
        target_country_code : TargetCountryCodeType
            _description_
        use_ship : bool
            _description_
        ship_own_fuel : bool
            _description_
        optimize_flh : bool
            _description_
        use_user_data_for_optimize_flh : bool, optional
            _description_, by default True

        Returns
        -------
        CalculateDataType
            _description_
        """
        data = self._get_calculation_data(
            secondary_processes=secondary_processes,
            chain_name=chain_name,
            process_code_res=process_code_res,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_ship=use_ship,
            ship_own_fuel=ship_own_fuel,
            use_user_data=True,
        )

        # get optimizedFLH?
        if optimize_flh:
            # if we have user data BUT it should NOT be used for optimization
            # get a different dataset for optimization
            if self.user_data is not None and not use_user_data_for_optimize_flh:
                data_opt = self._get_calculation_data(
                    secondary_processes=secondary_processes,
                    chain_name=chain_name,
                    process_code_res=process_code_res,
                    source_region_code=source_region_code,
                    target_country_code=target_country_code,
                    use_ship=use_ship,
                    ship_own_fuel=ship_own_fuel,
                    use_user_data=False,  # THIS IS THE IMPORTANT BIT
                )
            else:
                data_opt = data

            data = self.optimizer.get_data(data_opt, data)

        return data

    def _get_calculation_data(
        self,
        secondary_processes: Dict[FlowCodeType, ProcessCodeType],
        chain_name: ChainNameType,
        process_code_res: ProcessCodeResType,
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_ship: bool,
        ship_own_fuel: bool,
        use_user_data: bool = True,
    ) -> CalculateDataType:
        """Calculate results."""
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
            "context": {
                "source_region_code": source_region_code,
                "target_country_code": target_country_code,
            },
        }

        result["parameter"]["WACC"] = pg.get_parameter_value_w_default("WACC")
        result["parameter"]["CALOR"] = pg.get_parameter_value_w_default(
            parameter_code="CALOR", flow_code=chain["FLOW_OUT"]
        )

        # get transport distances and options
        # TODO? add these also to data
        dist_pipeline = pg.get_parameter_value_w_default("DST-S-DP", default=0)
        seashare_pipeline = pg.get_parameter_value_w_default("SEASHARE", default=0)
        existing_pipeline_cap = pg.get_parameter_value_w_default("CAP-T", default=0)
        dist_ship = pg.get_parameter_value_w_default("DST-S-D", default=0)

        if not use_ship and not chain["CAN_PIPELINE"]:
            use_ship = True

        transport_distances = self._get_transport_distances(
            source_region_code,
            target_country_code,
            use_ship,
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

        used_flows_secondary: set[FlowCodeType] = set()
        provided_flows_secondary: set[FlowCodeType] = set()
        for flow_code, process_code in secondary_processes.items():
            if not process_code:
                continue
            if flow_code not in used_flows_main_export:
                continue
            pp = pg.get_process_params(process_code)
            pp["process_code"] = process_code
            result["secondary_process"][flow_code] = pp
            used_flows_secondary = used_flows_secondary | set(pp["CONV"])
            provided_flows_secondary.add(flow_code)

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
        for process_step in chain_steps_main_import:
            process_code = chain[process_step]
            if not process_code:
                raise Exception((process_step, chain))
            pp = pg.get_process_params(process_code)
            pp["step"] = process_step
            pp["process_code"] = process_code
            result["main_import_process_chain"].append(pp)
            used_flows_main_import = used_flows_main_import | set(pp["CONV"])

            proc = self.dimensions["process"].loc[process_code]
            if proc.main_flow_code_in:
                used_flows_main_chain.add(proc.main_flow_code_in)
            if proc.main_flow_code_out:
                used_flows_main_chain.add(proc.main_flow_code_out)

        # If RES=Hybrid: we also need PV and Wind-On
        if process_code_res == "RES-HYBR":
            pc: ProcessCodeType
            for pc in ["PV-FIX", "WIND-ON"]:  # type:ignore
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
            | used_flows_main_import
        )
        # FIXME: used_flows_main_import may need to come from different country!!
        result["parameter"]["SPECCOST"] = pg.get_flow_params("SPECCOST", used_flows)

        return result

    @classmethod
    def get_dimensions_parameter_code(
        cls,
        dimension: DimensionType,
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
            flow_code = process["main_flow_code_out"]  # type:ignore
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
            chain["FLOW_OUT"],
        )

        return result_main_export, result_transport, result_main_import

    @staticmethod
    def _get_transport_distances(
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
        use_ship: bool,
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
                dist_transp["SHP_OWN"] = dist_ship
            else:
                dist_transp["SHP"] = dist_ship

        return dist_transp
