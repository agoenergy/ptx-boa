# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


import logging

import pandas as pd

from .api_calc import PtxCalc
from .api_data import DataHandler
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

logger = logging.getLogger()


class PtxboaAPI:
    def __init__(self, data_dir: str = None):
        self.data_dir = data_dir

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
        handler = DataHandler(scenario, user_data, data_dir=self.data_dir)
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
        ship_own_fuel: bool = False,  # TODO: no correctly passed by app
        output_unit: OutputUnitType = "USD/MWh",
        user_data: pd.DataFrame | None = None,
        optimize_flh: bool = False,
    ) -> pd.DataFrame:
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
        result : DataFrame
            columns are: most of the settings arguments of this function, and:

            * `values`: numerical value (usually cost)
            * `process_type`: one of {RESULT_PROCESS_TYPES}
            * `process_subtype`: arbitrary string
            * `cost_type`: one of {RESULT_COST_TYPES}

        """
        data_handler = DataHandler(scenario, user_data, data_dir=self.data_dir)

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

        return result_df
