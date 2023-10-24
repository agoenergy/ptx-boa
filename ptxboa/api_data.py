# -*- coding: utf-8 -*-
"""Handle data queries for api calculation."""

import pprint
from itertools import product

import numpy as np
import pandas as pd

from .data import load_data

PARAMETER_DIMENSIONS = {
    "CALOR": {"required": ["flow_code"], "global_default": False},
    "CAPEX": {
        "required": ["process_code", "source_region_code"],
        "global_default": True,
    },
    "CAP-T": {
        "required": ["source_region_code", "target_country_code"],
        "global_default": False,
    },
    "CONV": {"required": ["flow_code", "process_code"], "global_default": False},
    "DST-S-C": {"required": ["source_region_code"], "global_default": False},
    "DST-S-D": {
        "required": ["source_region_code", "target_country_code"],
        "global_default": False,
    },
    "DST-S-DP": {
        "required": ["source_region_code", "target_country_code"],
        "global_default": False,
    },
    "EFF": {"required": ["process_code"], "global_default": False},
    "FLH": {
        "required": [
            "process_code",
            "source_region_code",
            "process_code_res",
            "process_code_ely",
            "process_code_deriv",
        ],
        "global_default": False,
    },
    "LIFETIME": {"required": ["process_code"], "global_default": False},
    "LOSS-T": {"required": ["process_code"], "global_default": False},
    "OPEX-F": {
        "required": ["process_code", "source_region_code"],
        "global_default": True,
    },
    "OPEX-T": {"required": ["process_code"], "global_default": False},
    "RE-POT": {
        "required": ["process_code", "source_region_code"],
        "global_default": False,
    },
    "SEASHARE": {
        "required": ["source_region_code", "target_country_code"],
        "global_default": False,
    },
    "SPECCOST": {
        "required": ["flow_code", "source_region_code"],
        "global_default": True,
    },
    "WACC": {
        "required": ["process_code", "source_region_code"],
        "global_default": True,
    },
}


class PtxData:
    def __init__(self):
        self.dimensions = {
            dim: load_data(name=f"dim_{dim}")
            for dim in ["country", "flow", "parameter", "process", "region"]
        }
        self.flh = load_data(name="flh").set_index("key").replace(np.nan, "")
        self.chains = load_data(name="chains").set_index("chain").replace(np.nan, "")
        self.scenario_data = {
            f"{year} ({parameter_range})": load_data(name=f"{year}_{parameter_range}")
            .set_index("key")
            .replace(np.nan, "")
            for year, parameter_range in product(
                [2030, 2040], ["low", "medium", "high"]
            )
        }

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
        self._check_valid_scenario(scenario)

        scenario_data = self.scenario_data[scenario].copy()

        if long_names:
            for dim in ["parameter", "process", "flow", "region", "country"]:
                mapping = pd.Series(
                    self.dimensions[dim][f"{dim}_name"].to_list(),
                    index=self.dimensions[dim][f"{dim}_code"],
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

    def get_parameter_value(
        self,
        scenario,
        parameter_code,
        process_code=None,  # process_flh for flh
        flow_code=None,
        source_region_code=None,
        target_country_code=None,
        # only relevant for parameter FLH
        process_code_res=None,
        process_code_ely=None,
        process_code_deriv=None,
    ) -> float:
        """Get parameter value for processes."""
        self._check_required_kwargs(
            parameter_code,
            process_code=process_code,
            flow_code=flow_code,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            process_code_res=process_code_res,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
        )
        self._check_valid_scenario(scenario)

        if parameter_code == "FLH":
            df = self.flh
            selector = (
                (df["region"] == source_region_code)
                & (df["process_res"] == process_code_res)
                & (df["process_ely"] == process_code_ely)
                & (df["process_deriv"] == process_code_deriv)
                & (df["process_flh"] == process_code)
            )
        else:
            df = self.scenario_data[scenario]
            selector = df["parameter_code"] == parameter_code
            if process_code is not None:
                selector &= df["process_code"] == process_code
            if flow_code is not None:
                selector &= df["flow_code"] == flow_code
            if source_region_code is not None:
                selector &= df["source_region_code"] == source_region_code
            if target_country_code is not None:
                selector &= df["target_country_code"] == target_country_code

        row = df[selector]
        if len(row) == 0:
            raise ValueError("did not find a parameter value")
        if len(row) > 1:
            raise ValueError("found more than one parameter value")
        return row.squeeze().at["value"]

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

    def _get_scenario_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return pd.DataFrame(
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

    def _get_secproc_co2_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        df_proc = (
            self.dimensions["process"]
            .loc[self.dimensions["process"]["process_class"] == "PROV_C"]
            .copy()
        )
        df_proc = pd.concat(
            [df_proc, pd.DataFrame([{"process_name": "Specific costs"}])]
        )
        return df_proc.set_index("process_name", drop=False)

    def _get_secproc_water_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        df_proc = (
            self.dimensions["process"]
            .loc[self.dimensions["process"]["process_class"] == "PROV_H2O"]
            .copy()
        )
        df_proc = pd.concat(
            [df_proc, pd.DataFrame([{"process_name": "Specific costs"}])]
        )
        return df_proc.set_index("process_name", drop=False)

    def _get_chain_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return self.chains.copy()

    def _get_res_gen_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return (
            self.dimensions["process"]
            .loc[self.dimensions["process"]["process_class"] == "RE-GEN"]
            .copy()
            .set_index("process_name", drop=False)
        )

    def _get_region_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return self.dimensions["region"].set_index("region_name", drop=False)

    def _get_country_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return (
            self.dimensions["country"]
            .loc[self.dimensions["country"]["is_import"]]
            .set_index("country_name", drop=False)
        )

    def _get_transport_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return pd.DataFrame(
            [{"transport_name": "Ship"}, {"transport_name": "Pipeline"}]
        ).set_index("transport_name", drop=False)

    def _get_output_unit_dimension(self) -> pd.DataFrame:
        """Availible items for this class.

        Use index for dropdown selections
        """
        return pd.DataFrame(
            [{"unit_name": "USD/MWh"}, {"unit_name": "USD/t"}]
        ).set_index("unit_name", drop=False)

    def _check_required_kwargs(
        self,
        parameter_code: str,
        **kwargs,
    ):
        """
        Check parameters passed to `self.get_parameter_value()`.

        Check that required parameter dimensions are not None and that
        unused dimensions are None.

        Parameters
        ----------
        parameter_code : str
        kwargs :
            keyword arguments passed to `self.get_parameter_value()`
        """
        required_param_names = PARAMETER_DIMENSIONS[parameter_code]["required"]
        for p in required_param_names:
            required_value = kwargs.pop(p)
            if required_value is None:
                raise ValueError(
                    f"'{parameter_code}': the following parameters must be "
                    f"defined\n{required_param_names}"
                )

        # check that remaining unused kwargs are not defined
        if not all(value is None for value in kwargs.values()):
            raise ValueError(
                f"'{parameter_code}': irrelevant parameters"
                f" must be None but are currently\n{pprint.pformat(kwargs)}"
            )

    def _check_valid_scenario(self, scenario):
        if scenario not in self.scenario_data.keys():
            raise ValueError(
                f"No valid data scenario '{scenario}'. Possible values "
                f"are\n{list(self.scenario_data.keys())}"
            )


class DataHandler:
    def __init__(self, scenario, user_data):
        pass
