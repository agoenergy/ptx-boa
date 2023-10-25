# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


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
        user_data: dict = None,
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
            ids are expected to come as long names

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
        ship_own_fuel: bool,
        output_unit="USD/MWh",
        user_data: dict = None,
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
        user_data: pd.DataFrame
            user data that overrides scenario data
            contains only rows of scenario_data that have been modified.
            ids are expected to come as long names


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

        # TODO: better way to map dimension names to codes
        # self.data.map_name_to_code(dim, name) # noqa
        # self.data.map_code_to_name(name, code) # noqa
        def name_to_code_bad(dim, dim_name, name):
            df = self.data.get_dimension(dim)
            return df.loc[df[dim_name + "_name"] == name, dim_name + "_code"].iloc[0]

        result_df = calculator.calculate(
            secproc_co2_code=name_to_code_bad("secproc_co2", "process", secproc_co2),
            secproc_water_code=name_to_code_bad(
                "secproc_water", "process", secproc_water
            ),
            chain=chain,
            process_code_res=name_to_code_bad("res_gen", "process", res_gen),
            region_code=name_to_code_bad("region", "region", region),
            country_code=name_to_code_bad("country", "country", country),
            transport=transport,
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
