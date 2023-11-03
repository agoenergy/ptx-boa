# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


import logging

import pandas as pd

from .api_calc import calculate
from .api_data import DataHandler, DimensionCode, PtxData, ScenarioCode

logger = logging.getLogger()

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
    "Electricity and H2 storage",
]


class PtxboaAPI:
    """Singleton class for data and calculation api."""

    _inst = None

    def __new__(cls, *args, **kwargs):
        """Make sure class is only instantiated once."""
        if not cls._inst:
            cls._inst = super(PtxboaAPI, cls).__new__(cls, *args, **kwargs)
        else:
            logger.warning("Api should only be instantiated once")
        return cls._inst

    def __init__(self):
        self.data = PtxData()
        self._calc_counter = 0  # temporary counter for calls of calculate()

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
        ship_own_fuel: bool = False,  # TODO: no correctly passed by app
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

        # prepare / convert user settings to internal codes
        df_chain = data_handler.get_dimension("chain")
        df_process_by_name = data_handler.get_dimension("process").set_index(
            "process_name", drop=False
        )
        df_region_by_name = data_handler.get_dimension("region").set_index(
            "region_name", drop=False
        )
        df_country_by_name = data_handler.get_dimension("country").set_index(
            "country_name", drop=False
        )
        dct_chain = dict(df_chain.loc[chain])

        if transport not in {"Ship", "Pipeline"}:
            logger.error(f"Invalid choice for transport: {transport}")
        use_ship = transport == "Ship"

        secondary_processes = {
            "H2O-L": df_process_by_name.at[secproc_water, "process_code"]
            if secproc_water != "Specific costs"
            else None,
            "CO2-G": df_process_by_name.at[secproc_co2, "process_code"]
            if secproc_co2 != "Specific costs"
            else None,
        }
        process_code_res = df_process_by_name.at[res_gen, "process_code"]
        source_region_code = df_region_by_name.at[region, "region_code"]
        target_country_code = df_country_by_name.at[country, "country_code"]
        process_code_ely = dct_chain["ELY"]
        process_code_deriv = dct_chain["DERIV"]

        self._calc_counter += 1
        logger.info(
            "calculate #%s: %s=>%s",
            self._calc_counter,
            source_region_code,
            target_country_code,
        )

        # actual calculation
        result_df = calculate(
            data_handler,
            secondary_processes=secondary_processes,
            chain=dct_chain,
            process_code_res=process_code_res,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
            use_ship=use_ship,
            ship_own_fuel=ship_own_fuel,
        )

        # conversion to output unit
        if output_unit not in {"USD/MWh", "USD/t"}:
            logger.error(f"Invalid choice for output_unit: {output_unit}")
        conversion = 1000
        if output_unit == "USD/t":
            chain_flow_out = dct_chain["FLOW_OUT"]
            calor = data_handler.get_parameter_value(
                parameter_code="CALOR", flow_code=chain_flow_out
            )
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
