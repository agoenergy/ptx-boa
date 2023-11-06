# -*- coding: utf-8 -*-
"""Api for calculations for webapp."""

from itertools import product

import numpy as np
import pandas as pd
from pandas import DataFrame
from pandas.api.types import CategoricalDtype

from .data import load_data


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
        _dimensions = {
            "scenario": self._get_scenario_dimension,
            "secproc_co2": self._get_secproc_co2_dimension,
            "secproc_water": self._get_secproc_water_dimension,
            "chain": self._get_chain_dimension,
            "res_gen": self._get_res_gen_dimension,
            "region": self._get_region_dimension,
            "country": self._get_country_dimension,
            "transport": self._get_transport_dimension,
            "output_unit": self._get_output_unit_dimension,
        }
        return _dimensions[dim]()

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
        if scenario not in self.data_scenarios.keys():
            raise ValueError(
                f"No valid data scenario '{scenario}'. Possible values "
                f"are\n{list(self.data_scenarios.keys())}"
            )

        scenario_data = self.data_scenarios[scenario].copy()

        if long_names:
            for dim in ["parameter", "process", "flow", "region", "country"]:
                mapping = pd.Series(
                    self.dims[dim][f"{dim}_name"].to_list(),
                    index=self.dims[dim][f"{dim}_code"],
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

        if user_data is not None:
            # TODO: modify values based on user_data
            pass

        return scenario_data

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
        process_subtypes_mapping = {
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

        process_types = list(process_subtypes_mapping.keys())
        process_subtypes = [
            value for values in process_subtypes_mapping.values() for value in values
        ]
        cost_types = ["CAPEX", "OPEX", "FLOW", "LC"]

        df = (
            pd.MultiIndex.from_product(
                [process_subtypes, cost_types], names=["process_subtype", "cost_type"]
            )
            .to_frame()
            .reset_index(drop=True)
        )

        df["process_subtype"] = df["process_subtype"].astype(
            CategoricalDtype(categories=process_subtypes)
        )
        df["cost_type"] = df["cost_type"].astype(
            CategoricalDtype(categories=cost_types)
        )
        df["process_type"] = (
            df["process_subtype"]
            .map(
                {
                    value: key
                    for key, values in process_subtypes_mapping.items()
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
        result : dict
            keys are name of variables


        TODO: keys required in result dict

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
