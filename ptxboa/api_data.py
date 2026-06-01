"""Handle data queries for api calculation."""

from functools import cache
from itertools import product
from pathlib import Path
from typing import TYPE_CHECKING, Dict, List, Literal, Tuple

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
    DimensionType,
    FlowCodeType,
    OutputUnitValues,
    ParameterCodeType,
    ParameterRangeValues,
    ProcessCodeType,
    ProcessStepType,
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
)

if TYPE_CHECKING:
    from ptxboa.api_calc import PtxCalc


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


@cache
def _get_allowed_pipeline_routes() -> (
    set[tuple[SourceRegionCodeType, TargetCountryCodeType]]
):
    # pipeline distances is the same in all scenarios, so we take the first one.
    _df = _load_scenario_data(data_dir=DEFAULT_DATA_DIR, scenario=ScenarioValues[0])
    return {
        tuple(x)
        for x in _df.loc[
            _df["parameter_code"] == "DST-S-DP",
            ["source_region_code", "target_country_code"],
        ].values
    }


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


def _create_secproc_dimension(dimensions: dict[str, pd.DataFrame], process_class: str):
    return pd.concat(
        [
            dimensions["process"]
            .loc[dimensions["process"]["process_class"] == process_class]
            .copy(),
            pd.DataFrame([{"process_name": "Specific costs"}]),
        ]
    ).set_index("process_name", drop=False)


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
        process_res: ProcessCodeType | None = None,
        process_ely: ProcessCodeType | None = None,
        process_deriv: ProcessCodeType | None = None,
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
        process_res : str, optional
            Code for the process_res, by default None. Must be set for the
            following parameters:
                - FLH
        process_ely : str, optional
            Code for the process_ely, by default None. Must be set for the
            following parameters:
                - FLH
        process_deriv : str, optional
            Code for the process_deriv, by default None. Must be set for the
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
            "process_res": process_res or "",
            "process_ely": process_ely or "",
            "process_deriv": process_deriv or "",
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
                "process_res",
                "process_ely",
                "process_deriv",
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
            raise ValueError(f"""did not find a parameter value for:
                parameter_code={parameter_code},
                process_code={process_code},
                flow_code={flow_code},
                source_region_code={source_region_code},
                target_country_code={target_country_code},
                process_res={process_res},
                process_ely={process_ely},
                process_deriv={process_deriv}
                ({self.tool_version_color})
            """)
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
            "secproc_co2",
            "secproc_water",
        }:
            if tool_version_color == "blue":
                df = df.loc[df["is_blue"].astype(bool)]
            elif tool_version_color == "green":
                df = df.loc[df["is_green"].astype(bool)]

        return df

    def get_calculation_data(
        self,
        ptx_calc: "PtxCalc",
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
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
        data = ptx_calc.get_calculation_data(
            data_handler=self,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_user_data=True,
        )

        # get optimized FLH?
        if optimize_flh:
            # if we have user data BUT it should NOT be used for optimization
            # get a different dataset for optimization
            if self.user_data is not None and not use_user_data_for_optimize_flh:
                data_opt = ptx_calc.get_calculation_data(
                    data_handler=self,
                    source_region_code=source_region_code,
                    target_country_code=target_country_code,
                    use_user_data=False,  # THIS IS THE IMPORTANT BIT
                )

            else:
                data_opt = data

            data = self.optimizer.get_calculation_data(data_opt, data)

        return data

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

    @classmethod
    def get_chain_color(cls, chain: ChainType) -> ToolVersionColorType:
        """Get color from chain."""
        return "blue" if cls.dimensions["chain"].loc[chain, "is_blue"] else "green"

    @classmethod
    def correct_transport(
        cls,
        transport: TransportType,
        ship_own_fuel: bool,
        chain: ChainType,
        source_region_code: SourceRegionCodeType,
        target_country_code: TargetCountryCodeType,
    ) -> tuple[TransportType, bool]:
        """Validate / correct transport."""
        chain_data = cls.dimensions["chain"].loc[chain]
        if transport == "Pipeline" and not chain_data["can_pipeline"]:  # type: ignore
            logger.warning("Cannot use Pipeline - switching to Ship: %s", chain)
            transport = "Ship"

        # check if countries can pipeline
        if (
            transport == "Pipeline"
            and (source_region_code, target_country_code)
            not in _get_allowed_pipeline_routes()
        ):
            logger.warning(
                "Cannot use Pipeline - switching to Ship: %s => %s",
                source_region_code,
                target_country_code,
            )
            transport = "Ship"

        if ship_own_fuel and (transport != "Ship" or not bool(chain_data["SHP_OWN"])):
            logger.warning("Cannot use ship_own_fuel.")
            ship_own_fuel = False

        source_region_is_target_region = (
            source_region_code[:3] == target_country_code[:3]
        )
        if source_region_is_target_region:
            transport = "NONE"
            ship_own_fuel = False

        return transport, ship_own_fuel
