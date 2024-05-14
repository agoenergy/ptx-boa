# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


from pathlib import Path
from typing import List, Tuple

import pandas as pd
import pypsa

from ptxboa import logger

from . import PROFILES_DIR
from .api_calc import PtxCalc
from .api_data import DataHandler
from .api_optimize import PtxOpt
from .static import (
    ChainNameType,
    DimensionType,
    OutputUnitType,
    ResGenType,
    ScenarioType,
    SecProcCO2Type,
    SecProcH2OType,
    SourceRegionNameType,
    TargetCountryNameType,
    TransportType,
    TransportValues,
)


class PtxboaAPI:
    def __init__(self, data_dir: Path, cache_dir: Path = None):
        self.data_dir = data_dir
        self.cache_dir = cache_dir

    @staticmethod
    def get_dimension(dim: DimensionType) -> pd.DataFrame:
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
        return DataHandler.get_dimension(dim)

    def get_input_data(
        self,
        scenario: ScenarioType,
        long_names: bool = True,
        user_data: pd.DataFrame | None = None,
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
        )
        return handler.get_input_data(long_names)

    def calculate(
        self,
        scenario: ScenarioType,
        secproc_co2: SecProcCO2Type,
        secproc_water: SecProcH2OType,
        chain: ChainNameType,
        res_gen: ResGenType,
        region: SourceRegionNameType,
        country: TargetCountryNameType,
        transport: TransportType,
        ship_own_fuel: bool,
        output_unit: OutputUnitType = "USD/MWh",
        user_data: pd.DataFrame | None = None,
        optimize_flh: bool = False,
    ) -> Tuple[pd.DataFrame, object]:
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

        Returns
        -------
        result : (DataFrame, metadata)
            columns are: most of the settings arguments of this function, and:

            * `values`: numerical value (usually cost)
            * `process_type`: one of {RESULT_PROCESS_TYPES}
            * `process_subtype`: arbitrary string
            * `cost_type`: one of {RESULT_COST_TYPES}

        """
        data_handler = DataHandler(
            scenario, user_data, data_dir=self.data_dir, cache_dir=self.cache_dir
        )

        if transport not in TransportValues:
            logger.error(f"Invalid choice for transport: {transport}")

        data = data_handler.get_calculation_data(
            secondary_processes={
                "H2O-L": (
                    DataHandler.get_dimensions_parameter_code(
                        "secproc_water", secproc_water
                    )
                    if secproc_water
                    else None
                ),
                "CO2-G": (
                    DataHandler.get_dimensions_parameter_code(
                        "secproc_co2", secproc_co2
                    )
                    if secproc_co2
                    else None
                ),
            },
            chain_name=chain,
            process_code_res=DataHandler.get_dimensions_parameter_code(
                "res_gen", res_gen
            ),
            source_region_code=DataHandler.get_dimensions_parameter_code(
                "region", region
            ),
            target_country_code=DataHandler.get_dimensions_parameter_code(
                "country", country
            ),
            use_ship=(transport == "Ship"),
            ship_own_fuel=ship_own_fuel,
            optimize_flh=optimize_flh,
        )

        result_df = PtxCalc.calculate(data)

        # conversion to output unit
        if output_unit not in {"USD/MWh", "USD/t"}:
            logger.error(f"Invalid choice for output_unit: {output_unit}")
        conversion = 1000
        if output_unit == "USD/t":
            calor = data["parameter"]["CALOR"]
            conversion *= calor
        result_df["values"] = result_df["values"] * conversion

        # add user settings
        result_df["scenario"] = scenario
        result_df["secproc_co2"] = secproc_co2
        result_df["secproc_water"] = secproc_water
        result_df["chain"] = chain
        result_df["res_gen"] = res_gen
        result_df["region"] = region
        result_df["country"] = country
        result_df["transport"] = transport

        metadata = {"flh_opt_hash": data.get("flh_opt_hash")}  # does not always exist
        return result_df, metadata

    def get_flh_opt_network(
        self,
        scenario: ScenarioType,
        secproc_co2: SecProcCO2Type,
        secproc_water: SecProcH2OType,
        chain: ChainNameType,
        res_gen: ResGenType,
        region: SourceRegionNameType,
        country: TargetCountryNameType,
        transport: TransportType,
        ship_own_fuel: bool,
        user_data: pd.DataFrame | None = None,
    ) -> Tuple[pypsa.Network, dict]:
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
        _df, metadata = self.calculate(
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
        )
        hashsum = metadata.get("flh_opt_hash", {}).get("hash_md5")
        if not hashsum:
            return None

        data_handler = DataHandler(
            scenario, user_data, data_dir=self.data_dir, cache_dir=self.cache_dir
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
