# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""

from itertools import product
from typing import Dict

import numpy as np
import pandas as pd
from pandas import DataFrame

from .data import load_context_data, load_data


class PtxboaAPI:
    def __init__(self):
        """Instance creation loads all data from local files."""
        self.dims = {
            dim: load_data(name=f"dim_{dim}")
            for dim in ["country", "flow", "parameter", "process", "region"]
        }
        self.df_data_flh = load_data(name="flh").set_index("key").replace(np.nan, "")
        self.df_chains = load_data(name="chains").set_index("chain").replace(np.nan, "")
        self.data_scenarios = {
            f"{year} ({parameter_range})": load_data(name=f"{year}_{parameter_range}")
            .set_index("key")
            .replace(np.nan, "")
            for year, parameter_range in product(
                [2030, 2040], ["low", "medium", "high"]
            )
        }

    def get_dimensions(self) -> Dict[str, pd.DataFrame]:
        """Return dimension elements to populate app dropdowns.

        Returns
        -------
        : dict
            mapping keys identifying the dimension and values holding the data as
            :class:`pd.DataFrame`. The following dimension keys are available:
                - 'scenario'
                - 'secproc_co2'
                - 'secproc_water'
                - 'chain'
                - 'res_gen'
                - 'region'
                - 'country'
                - 'transport'
                - 'output_unit'
        """
        return {
            "scenario": self._get_scenario_dimension(),
            "secproc_co2": self._get_secproc_co2_dimension(),
            "secproc_water": self._get_secproc_water_dimension(),
            "chain": self._get_chain_dimension(),
            "res_gen": self._get_res_gen_dimension(),
            "region": self._get_region_dimension(),
            "country": self._get_country_dimension(),
            "transport": self._get_transport_dimension(),
            "output_unit": self._get_output_unit_dimension(),
        }

    def get_input_data(
        self,
        scenario: str,
        user_data: dict = None,
    ) -> dict:
        """Return scenario data.

        if user data is defined, specified values will be replaced with those.
        if global defaults for countries exists, we return expanded data
        for all countries.

        Parameters
        ----------
        scenario : str
            name of data scenario
        user_data : dict, optional
            user data that overrides scenario data

        Returns
        -------
        : dict
            mapping of parameter names to data frames

        """
        return {}

    def calculate(
        self,
        scenario: str,
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
    ) -> dict:
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
        user_data: dict
            user data that overrides scenario data


        Returns
        -------
        result : dict
            keys are name of variables


        TODO: keys required in result dict

        """
        return {}

    def _get_scenario_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return DataFrame(
            [
                {
                    "year": year,
                    "parameter_range": parameter_range,
                    "scenario_name": f"{year} ({parameter_range})",
                }
                for year, parameter_range in product(
                    [2030, 2040], ["low", "medium", "high"]
                )
            ]
        ).set_index("scenario_name")

    def _get_secproc_co2_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        df_proc = (
            self.dims["process"]
            .loc[self.dims["process"]["process_class"] == "PROV_C"]
            .copy()
        )
        df_proc = pd.concat(
            [df_proc, pd.DataFrame([{"process_name": "Specific costs"}])]
        )
        return df_proc.set_index("process_name", drop=False)

    def _get_secproc_water_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        df_proc = (
            self.dims["process"]
            .loc[self.dims["process"]["process_class"] == "PROV_H2O"]
            .copy()
        )
        df_proc = pd.concat(
            [df_proc, pd.DataFrame([{"process_name": "Specific costs"}])]
        )
        return df_proc.set_index("process_name", drop=False)

    def _get_chain_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return self.df_chains.copy()

    def _get_res_gen_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return (
            self.dims["process"]
            .loc[self.dims["process"]["process_class"] == "RE-GEN"]
            .copy()
            .set_index("process_name", drop=False)
        )

    def _get_region_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return self.dims["region"].set_index("region_name", drop=False)

    def _get_country_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return (
            self.dims["country"]
            .loc[self.dims["country"]["is_import"]]
            .set_index("country_name", drop=False)
        )

    def _get_transport_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return DataFrame(
            [{"transport_name": "Ship"}, {"transport_name": "Pipeline"}]
        ).set_index("transport_name", drop=False)

    def _get_output_unit_dimension(self) -> DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return DataFrame([{"unit_name": "USD/MWh"}, {"unit_name": "USD/t"}]).set_index(
            "unit_name", drop=False
        )

    def load_context_data(self, name: str) -> pd.DataFrame:
        """Load context data."""
        return load_context_data(name)
