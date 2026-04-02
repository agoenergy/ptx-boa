"""Api for calculations for webapp."""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import pandas as pd
import pypsa

from ptxboa import PROFILES_DIR, logger
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DataHandler, correct_transport, get_chain_color
from ptxboa.api_optimize import PtxOpt
from ptxboa.process_classes import ChainProcess
from ptxboa.static import (
    ChainType,
    DimensionType,
    FlowCodeType,
    OutputUnitType,
    ProcessCodeType,
    ResGenType,
    ScenarioType,
    SecProcCO2Type,
    SecProcH2OType,
    SourceRegionNameType,
    TargetCountryNameType,
    ToolVersionColorType,
    TransportType,
    TransportValues,
)
from ptxboa.static._type_defs import ChainDef, PtxCalcResult


@dataclass(slots=True, frozen=True)
class ApiCalculateResult:
    costs: pd.DataFrame
    metadata: dict
    emissions: Optional[pd.DataFrame] = None
    emission_mass: Optional[pd.DataFrame] = None
    todo_results_flows: Optional[list] = None
    todo_data: Optional[object] = None
    todo_df_results_cost_unscaled: Optional[pd.DataFrame] = None


class PtxboaAPI:
    """Main API class."""

    def __init__(self, data_dir: Path, cache_dir: Path | None = None):
        self.data_dir = data_dir
        self.cache_dir = cache_dir

    @staticmethod
    def get_dimension(
        dim: DimensionType, tool_version_color: ToolVersionColorType | None = None
    ) -> pd.DataFrame:
        """Return a dimension element to populate app dropdowns.

        Parameters
        ----------
        dim : str
            Dimesion name. The following dimensions are available:
                - 'scenario'
                - 'secproc_co2'
                - 'secproc_water'
                - 'chain'
                - 'res_gen'
                - 'region'
                - 'country'
                - 'transport'
                - 'output_unit'
                - 'process'
                - 'flow'

        Returns
        -------
        : pd.DataFrame
            The dimension the data as
        """
        return DataHandler.get_dimension(dim, tool_version_color=tool_version_color)

    def get_input_data(
        self,
        scenario: ScenarioType,
        long_names: bool = True,
        user_data: pd.DataFrame | None = None,
        tool_version_color: ToolVersionColorType = "green",
    ) -> pd.DataFrame:
        """Return scenario data.

        if user data is defined, specified values will be replaced with those.
        if global defaults for countries exists, we return expanded data
        for all countries.

        Parameters
        ----------
        scenario : str
            name of data scenario. Possible values:
                - '2030 (low)'
                - '2030 (medium)'
                - '2030 (high)'
                - '2040 (low)'
                - '2040 (medium)'
                - '2040 (high)'
        long_names : bool, optional
            if True, will replace the codes used internally with long names that are
            used in the frontend.
        user_data : pd.DataFrame | None, optional
            user data that overrides scenario data
            contains only rows of scenario_data that have been modified.
            ids are expected to come as long names. Needs to have the columns
            "source_region_code", "process_code", "parameter_code", "flow_code", and
            "value".

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        handler = DataHandler(
            scenario,
            user_data,
            data_dir=self.data_dir,
            cache_dir=None,  # dont need caching for input data
            tool_version_color=tool_version_color,
        )
        return handler.get_input_data(long_names)

    def calculate(
        self,
        scenario: ScenarioType,
        secproc_co2: SecProcCO2Type | None,
        secproc_water: SecProcH2OType | None,
        chain: ChainType,
        res_gen: ResGenType | None,
        region: SourceRegionNameType,
        country: TargetCountryNameType,
        transport: TransportType,
        ship_own_fuel: bool,
        output_unit: OutputUnitType = "USD/MWh",
        user_data: pd.DataFrame | None = None,
        optimize_flh: bool = True,
        use_user_data_for_optimize_flh: bool = False,
        tool_version_color: ToolVersionColorType = "green",
    ) -> ApiCalculateResult:
        """Calculate results based on user selection.

        Parameters
        ----------
        scenario : str
            name of data scenario
        secproc_co2 : str
            name of secondary process for CO2
        secproc_water : str
            name of secondary process for H2O
        chain : str
            name of product chain
        res_gen : str
            name of renewable technology
        region : str
            name of region
        country : str
            name of destination country
        transport : str
            mode of transportation
        ship_own_fuel : bool
            `True` if ship uses product as fuel
        output_unit : str, optional
            output unit
        user_data : pd.DataFrame | None, optional
            user data that overrides scenario data
            contains only rows of scenario_data that have been modified.
            ids are expected to come as long names. Needs to have the columns
            ["source_region_code", "process_code", "parameter_code", "value"].
        use_user_data_for_optimize_flh: bool
            If True: use user data as input for flh optimization as well.
        tool_version_color: str
            "green" or "blue"

        Returns
        -------
        result : (DataFrame, metadata)
            columns are: most of the settings arguments of this function, and:

            * `values`: numerical value (usually cost)
            * `process_type`: one of {RESULT_PROCESS_TYPES}
            * `process_subtype`: arbitrary string
            * `cost_type`: one of {RESULT_COST_TYPES}

        """
        # validate and translate user settings
        chain_def, tool_version_color, optimize_flh = (
            _translate_and_validate_user_settings(
                secproc_co2=secproc_co2,
                secproc_water=secproc_water,
                chain=chain,
                res_gen=res_gen,
                region=region,
                country=country,
                transport=transport,
                ship_own_fuel=ship_own_fuel,
                optimize_flh=optimize_flh,
                tool_version_color=tool_version_color,
            )
        )

        # create data handler and get data
        data_handler = DataHandler(
            scenario,
            user_data,
            data_dir=self.data_dir,
            cache_dir=self.cache_dir,
            tool_version_color=tool_version_color,
        )
        chain_proc = ChainProcess.get_or_create(chain_def)

        data = data_handler.get_calculation_data(
            chain_def=chain_def,
            optimize_flh=optimize_flh,
            use_user_data_for_optimize_flh=use_user_data_for_optimize_flh,
            chain_proc=chain_proc,  # NEW
        )

        # calculate results
        # FIXME: replace PtxCalc.calculate with chain_proc.calculate
        ptxcalc_result = chain_proc.calculate(data)  # NEW
        ptxcalc_result = PtxCalc.calculate(data)

        # convert to output unit
        df_results_cost_unscaled = ptxcalc_result.df_results_cost.copy()
        _convert_to_output_unit_inplace(
            ptxcalc_result,
            output_unit=output_unit,
            chain=chain,
            calor=data["parameter"]["CALOR"],
        )

        # add user settings
        for df in [
            ptxcalc_result.df_results_cost,
            ptxcalc_result.df_results_emissions_e_g_co2e,
            ptxcalc_result.df_results_emissions_m_g_co2e,
        ]:
            df["scenario"] = scenario
            df["secproc_co2"] = secproc_co2
            df["secproc_water"] = secproc_water
            df["chain"] = chain
            df["res_gen"] = res_gen
            df["region"] = region
            df["country"] = country
            df["transport"] = transport

        # structure output

        metadata = {"flh_opt_hash": data.get("flh_opt_hash")}  # does not always exist

        # combine main flows with secondary flows
        todo_results_flows = ptxcalc_result.results_flows_chain or []
        for d in ptxcalc_result.results_flows_secondary or []:
            d = d.copy()
            d["process_step"] = "SECONDARY:" + d["process_step"]
            todo_results_flows += [d]

        return ApiCalculateResult(
            metadata=metadata,
            costs=ptxcalc_result.df_results_cost,
            emissions=ptxcalc_result.df_results_emissions_e_g_co2e,
            emission_mass=ptxcalc_result.df_results_emissions_m_g_co2e,
            todo_results_flows=todo_results_flows,
            todo_data=data,
            todo_df_results_cost_unscaled=df_results_cost_unscaled,
        )

    def get_flh_opt_network(
        self,
        scenario: ScenarioType,
        secproc_co2: SecProcCO2Type,
        secproc_water: SecProcH2OType,
        chain: ChainType,
        res_gen: ResGenType,
        region: SourceRegionNameType,
        country: TargetCountryNameType,
        transport: TransportType,
        ship_own_fuel: bool,
        user_data: pd.DataFrame | None = None,
    ) -> Tuple[pypsa.Network, dict] | None:
        """Calculate results based on user selection.

        Parameters
        ----------
        scenario : str
            name of data scenario
        secproc_co2 : str
            name of secondary process for CO2
        secproc_water : str
            name of secondary process for H2O
        chain : str
            name of product chain
        res_gen : str
            name of renewable technology
        region : str
            name of region
        country : str
            name of destination country
        transport : str
            mode of transportation
        ship_own_fuel : bool
            `True` if ship uses product as fuel
        user_data : pd.DataFrame | None, optional
            user data that overrides scenario data
            contains only rows of scenario_data that have been modified.
            ids are expected to come as long names. Needs to have the columns
            ["source_region_code", "process_code", "parameter_code", "value"].

        Returns
        -------
        result : Tuple[pypsa-Network, dict]
            second part of tuple contains metadata
        """
        metadata = self.calculate(
            scenario=scenario,
            secproc_co2=secproc_co2,
            secproc_water=secproc_water,
            chain=chain,
            res_gen=res_gen,
            region=region,
            country=country,
            transport=transport,
            ship_own_fuel=ship_own_fuel,
            user_data=user_data,
            optimize_flh=True,
            use_user_data_for_optimize_flh=True,  # always consider user data
        ).metadata
        hashsum = metadata.get("flh_opt_hash", {}).get("hash_md5")
        if not hashsum:
            return None

        data_handler = DataHandler(
            scenario,
            user_data,
            data_dir=self.data_dir,
            cache_dir=self.cache_dir,
            tool_version_color="green",  # no optimization in blue tool
        )
        filepath = data_handler.optimizer._get_cache_filepath(hashsum=hashsum)
        network = data_handler.optimizer._load_network(filepath=filepath)
        return network

    def get_res_technologies(
        self, region_name: SourceRegionNameType
    ) -> List[ResGenType]:
        """List all available RES technologies for a source region.

        Parameters
        ----------
        region_name: SourceRegionNameType

        Returns
        -------
        : List[ResGenType]

        """
        optimizer = PtxOpt(profiles_path=PROFILES_DIR, cache_dir=None)

        # translate name -> code
        region_code = DataHandler.get_dimensions_parameter_code("region", region_name)

        # get all keys from profiles
        reg_res = set(optimizer.profiles_hashes.data.keys())
        # filter keys for selected source_region
        res_techs = pd.Series([res for reg, res in reg_res if reg == region_code])

        # translate code -> name
        res_gen = self.get_dimension("res_gen")
        res_gen_code_to_name = pd.Series(
            res_gen["process_name"].to_list(),
            index=res_gen["process_code"],
        )
        res_techs = res_techs.map(res_gen_code_to_name).to_list()
        return res_techs

    def get_optimization_flh_input_data(self, long_names: bool = True) -> pd.DataFrame:
        """
        Return full load hours of renewables used by the optimization.

        Parameters
        ----------
        long_names : bool, optional
            Whether to return long names or internal codes, by default True

        Returns
        -------
        : pd.DataFrame
            long format data
            columns: source_region, res_gen, value
        """
        optimizer = PtxOpt(profiles_path=PROFILES_DIR, cache_dir=None)
        data = optimizer.profiles_flh.data.copy()
        if long_names:
            regions = self.get_dimension("region")
            region_code_to_name = pd.Series(
                regions["region_name"].to_list(),
                index=regions["region_code"],
            )
            data["source_region"] = data["source_region"].map(region_code_to_name)

            res_gen = self.get_dimension("res_gen")
            res_gen_code_to_name = pd.Series(
                res_gen["process_name"].to_list(),
                index=res_gen["process_code"],
            )
            # TODO: we could define names and codes in ptxboa\static\dim_process.csv
            # process_code, process_name
            # RES-HYBR-PV-FIX, PV tilted (hybrid)
            # RES-HYBR-WIND-ON, Wind Onshore (hybrid)
            # hard coded names for hybrid location:
            res_gen_code_to_name["RES-HYBR-PV-FIX"] = "PV tilted (hybrid)"
            res_gen_code_to_name["RES-HYBR-WIND-ON"] = "Wind Onshore (hybrid)"

            data["res_gen"] = data["res_gen"].map(res_gen_code_to_name)
            return data

        else:
            return data


def _translate_and_validate_user_settings(
    secproc_co2: SecProcCO2Type | None,
    secproc_water: SecProcH2OType | None,
    chain: ChainType,
    res_gen: ResGenType | None,
    region: SourceRegionNameType,
    country: TargetCountryNameType,
    transport: TransportType,
    ship_own_fuel: bool,
    optimize_flh: bool = True,
    tool_version_color: ToolVersionColorType = "green",
    **_,  # allow others - unused
) -> tuple[ChainDef, ToolVersionColorType, bool]:
    chain_data = DataHandler.get_dimension("chain").loc[chain]

    # check tool_version_color
    tool_version_color_chain = get_chain_color(chain)
    if tool_version_color_chain != tool_version_color:
        logger.error(
            "Chain is %s => changing tool_version_color from %s",
            tool_version_color_chain,
            tool_version_color,
        )
        tool_version_color = tool_version_color_chain

    if tool_version_color == "green" and not res_gen:
        raise Exception("No RES defined.")

    # check optimize_flh: make sure optimize_flh=False in blue tool
    if optimize_flh and tool_version_color == "blue":
        logger.warning("optimize_flh should be False in blue tool.")
        optimize_flh = False

    # check transport
    if transport not in TransportValues:
        logger.error(f"Invalid choice for transport: {transport}")

    transport, ship_own_fuel = correct_transport(transport, ship_own_fuel, chain)

    # CSS defined in chain

    secproc_ccs = chain_data["CO2_TS"]
    secproc_ccs_i = chain_data["CO2_TS_I"]

    # in API, we pass names, not codes
    df_proc = DataHandler.get_dimension("process")
    if secproc_ccs:
        secproc_ccs = df_proc.loc[secproc_ccs, "process_name"]
    if secproc_ccs_i:
        secproc_ccs_i = df_proc.loc[secproc_ccs_i, "process_name"]

    if tool_version_color == "blue":
        secproc_heat = "Large scale Heatpump (blue)"
        secproc_el = "Combined Cycle Gas Turbine with CCS (blue)"
    else:
        secproc_heat = None
        secproc_el = None

    secondary_processes: dict[FlowCodeType, ProcessCodeType] = {}
    for flow_code, dimension, parameter_name in [
        ("H2O-L", "secproc_water", secproc_water),
        ("CO2-G", "secproc_co2", secproc_co2),
        ("HEAT", "secproc_heat", secproc_heat),
        ("EL", "secproc_el", secproc_el),
        ("CO2-C", "secproc_ccs", secproc_ccs or secproc_ccs_i),
    ]:
        if not parameter_name or parameter_name == "Specific costs":
            continue

        process_code = DataHandler.get_dimensions_parameter_code(
            dimension=dimension,
            parameter_name=parameter_name,
        )
        if not process_code:
            raise Exception(f"Invalid process: {parameter_name}")

        secondary_processes[flow_code] = process_code  # type: ignore

    chain_def = ChainDef(
        chain_name=chain,
        secondary_processes=secondary_processes,
        process_code_res=DataHandler.get_dimensions_parameter_code("res_gen", res_gen),  # type: ignore # noqa
        source_region_code=DataHandler.get_dimensions_parameter_code("region", region),  # type: ignore # noqa
        target_country_code=DataHandler.get_dimensions_parameter_code(  # type: ignore # noqa
            "country", country
        ),
        transport=transport,
        ship_own_fuel=ship_own_fuel,
    )

    return chain_def, tool_version_color, optimize_flh


def _convert_to_output_unit_inplace(
    ptxcalc_result: PtxCalcResult,
    output_unit: OutputUnitType,
    chain: ChainType,
    calor: float,
) -> None:
    # conversion to output unit
    if output_unit not in {"USD/MWh", "USD/t"}:
        logger.error(f"Invalid choice for output_unit: {output_unit}")

    flow_code_chain_out = DataHandler.get_dimension("chain").loc[chain, "flow_out"]
    flow_unit_chain_out = DataHandler.get_dimension("flow").loc[
        flow_code_chain_out, "unit"
    ]  # type: ignore

    if flow_unit_chain_out.lower().startswith("kwh"):
        if output_unit == "USD/MWh":
            conversion = 1000  # kWh -> MWh
        else:
            conversion = 1000 * calor  # kWh -> kg and kg -> t
    elif flow_unit_chain_out.lower().startswith("kg"):
        if output_unit == "USD/t":
            conversion = 1000  # kg -> t
        else:
            conversion = 1000 / calor  # kg -> kWh -> Mwh
    else:
        raise ValueError("chain output unit must be either kWh or kg")

    for df in [
        ptxcalc_result.df_results_cost,
        ptxcalc_result.df_results_emissions_e_g_co2e,
        ptxcalc_result.df_results_emissions_m_g_co2e,
    ]:
        df["values"] = df["values"] * conversion
