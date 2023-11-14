# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


import logging

import pandas as pd

from .api_calc import PtxCalc
from .api_data import DataHandler, DimensionCode, PtxData, ScenarioCode

RESULT_COST_TYPES = ["CAPEX", "OPEX", "FLOW", "LC"]
RESULT_PROCESS_TYPES = [
    "Water",
    "Electrolysis",
    "Electricity generation",
    "Transportation (Pipeline)",
    "Transportation (Ship)",
    "Carbon",
    "Derivate production",
    "Heat",
]


class PtxboaAPI:
    def __init__(self):
        self.data = PtxData()

    def get_dimension(self, dim: DimensionCode) -> pd.DataFrame:
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

        Returns
        -------
        : pd.DataFrame
            The dimension the data as
        """
        return self.data.get_dimension(dim)

    def get_input_data(
        self,
        scenario: ScenarioCode,
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
            ["source_region_code", "process_code", "parameter_code", "value"].

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        handler = DataHandler(self.data, scenario, user_data)
        return handler.get_input_data(long_names)

    def calculate(
        self,
        scenario: ScenarioCode,
        secproc_co2: str,
        secproc_water: str,
        chain: str,
        res_gen: str,
        region: str,
        country: str,
        transport: str,
        ship_own_fuel: bool = False,  # TODO: no correctly passed by app
        output_unit="USD/MWh",
        user_data: pd.DataFrame | None = None,
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
        data_handler = DataHandler(self.data, scenario, user_data)

        calculator = PtxCalc(data_handler)

        if transport not in {"Ship", "Pipeline"}:
            logging.error("Invalid choice for transport")
        use_ship = transport == "Ship"

        result_df = calculator.calculate(
            secproc_co2_code=self.data.get_dimensions_parameter_code(
                "secproc_co2", secproc_co2
            ),
            secproc_water_code=self.data.get_dimensions_parameter_code(
                "secproc_water", secproc_water
            ),
            chain=chain,
            process_code_res=self.data.get_dimensions_parameter_code(
                "res_gen", res_gen
            ),
            source_region_code=self.data.get_dimensions_parameter_code(
                "region", region
            ),
            target_country_code=self.data.get_dimensions_parameter_code(
                "country", country
            ),
            use_ship=use_ship,
            ship_own_fuel=ship_own_fuel,
            output_unit=output_unit,
        )

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
