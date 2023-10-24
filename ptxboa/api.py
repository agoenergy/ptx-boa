# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""


import numpy as np
import pandas as pd
from pandas.api.types import CategoricalDtype

from .api_data import PtxData

COST_TYPES = ["CAPEX", "OPEX", "FLOW", "LC"]
PROCESS_SUBTYPES_MAPPING = {
    "Water": [
        "ely_h2o",
        "ely_fl_h2o",
        "deriv_h2o",
        "deriv_fl_h2o",
        "deriv_h2o_fl_h2o",
        "deriv_h2o_fl_el",
        "ely_h2o_fl_el",
    ],
    "Electrolysis": ["ely", "ely_fl_el"],
    "Electricity generation": ["res"],
    "Transportation (Pipeline)": [
        "tr_pre_ppl",
        "tr_ppl",
        "tr_pplx",
        "tr_ppls",
        "tr_pplr",
        "tr_post_ppl_fl_el",
        "tr_pre_ppl_fl_el",
        "tr_post_ppl",
    ],
    "Transportation (Ship)": [
        "tr_shp",
        "tr_pre_shp",
        "tr_post_shp",
        "tr_post_shp_fl_el",
        "tr_pre_shp_fl_el",
        "tr_shp_fl_bfuel",
    ],
    "Carbon": ["deriv_fl_co2", "deriv_co2", "deriv_co2_fl_el"],
    "Derivate production": ["deriv", "deriv_fl_el", "deriv_fl_n2"],
    "Heat": [
        "ely_h2o_fl_heat",
        "deriv_h2o_fl_heat",
        "deriv_co2_fl_heat",
        "deriv_fl_heat",
        "tr_post_ppl_fl_heat",
        "tr_post_shp_fl_heat",
    ],
}

# all types from mapping
PROCESS_TYPES = list(PROCESS_SUBTYPES_MAPPING)
# all subtypes from mapping
PROCESS_SUBTYPES = list({t for tst in PROCESS_SUBTYPES_MAPPING.values() for t in tst})


class PtxboaAPI:
    def __init__(self):
        self.data = PtxData()

    def get_dimension(self, dim: str) -> pd.DataFrame:
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
        scenario: str,
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
        user_data : dict, optional
            user data that overrides scenario data

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        return self.data.get_input_data(scenario, long_names, user_data)

    def _create_random_output_data(
        self,
        scenario: str,
        secproc_co2: str,
        secproc_water: str,
        chain: str,
        res_gen: str,
        region: str,
        country: str,
        transport: str,
    ) -> pd.DataFrame:
        """
        Create random output data as a long format dataframe.

        The output contains the used setting as categorical "index" columns and one
        "values" column with randomly generated results.
        """
        settings = {
            "scenario": scenario,
            "secproc_co2": secproc_co2,
            "secproc_water": secproc_water,
            "chain": chain,
            "res_gen": res_gen,
            "region": region,
            "country": country,
            "transport": transport,
        }

        # all process_subtypes are listed for each process_type

        process_types = list(PROCESS_SUBTYPES_MAPPING.keys())
        process_subtypes = [
            value for values in PROCESS_SUBTYPES_MAPPING.values() for value in values
        ]

        df = (
            pd.MultiIndex.from_product(
                [process_subtypes, COST_TYPES], names=["process_subtype", "cost_type"]
            )
            .to_frame()
            .reset_index(drop=True)
        )

        df["process_subtype"] = df["process_subtype"].astype(
            CategoricalDtype(categories=process_subtypes)
        )
        df["cost_type"] = df["cost_type"].astype(
            CategoricalDtype(categories=COST_TYPES)
        )
        df["process_type"] = (
            df["process_subtype"]
            .map(
                {
                    value: key
                    for key, values in PROCESS_SUBTYPES_MAPPING.items()
                    for value in values
                }
            )
            .astype(CategoricalDtype(categories=process_types))
        )

        for dim in [
            "scenario",
            "secproc_co2",
            "secproc_water",
            "chain",
            "res_gen",
            "region",
            "country",
            "transport",
        ]:
            # initialize categorical columns with all possible category values for each
            # dimension
            df[dim] = pd.Categorical(
                [settings[dim]] * len(df),
                categories=self.get_dimension(dim).index.tolist(),
            )

        df["values"] = np.random.rand(len(df))
        return df

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
        user_data: dict
            user data that overrides scenario data


        Returns
        -------
        result : DataFrame
            columns are: most of the settings arguments of this function, and:

            * `values`: numerical value (usually cost)
            * `process_type`: one of PROCESS_TYPES
            * `process_subtype`: one of PROCESS_SUBTYPES
            * `cost_type`: one of COST_TYPES

        """
        return self._create_random_output_data(
            scenario,
            secproc_co2,
            secproc_water,
            chain,
            res_gen,
            region,
            country,
            transport,
        )
