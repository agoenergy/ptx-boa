# -*- coding: utf-8 -*-
"""Handle data queries for api calculation."""

import logging
from itertools import product
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _load_data(data_dir, name: str) -> pd.DataFrame:
    filepath = Path(data_dir) / f"{name}.csv"
    df = pd.read_csv(filepath)
    # numerical columns should never be empty, dimension columns
    # maybe empty and will be filled with ""
    df = df.fillna("")
    return df


DATA_DIR = Path(__file__).parent / "data"

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
            # the following are not required for RES:
            # "process_code_res",
            # "process_code_ely",
            # "process_code_deriv",
        ],
        "global_default": False,
    },
    "LIFETIME": {"required": ["process_code"], "global_default": False},
    "LOSS-T": {"required": ["process_code"], "global_default": False},
    "OPEX-F": {
        "required": ["process_code", "source_region_code"],
        "global_default": True,
    },
    "OPEX-O": {
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
        "required": ["source_region_code"],
        "global_default": True,
    },
    "STR-CF": {
        "required": [],
        "global_default": False,
    },
}

ParameterCode = Literal[
    "CALOR",
    "CAPEX",
    "CAP-T",
    "CONV",
    "DST-S-C",
    "DST-S-D",
    "DST-S-DP",
    "EFF",
    "FLH",
    "LIFETIME",
    "LOSS-T",
    "OPEX-F",
    "OPEX-T",
    "RE-POT",
    "SEASHARE",
    "SPECCOST",
    "WACC",
    "STR-CF",
]
ScenarioCode = Literal[
    "2030 (low)",
    "2030 (medium)",
    "2030 (high)",
    "2040 (low)",
    "2040 (medium)",
    "2040 (high)",
]
DimensionCode = Literal[
    "scenario",
    "secproc_co2",
    "secproc_water",
    "chain",
    "res_gen",
    "region",
    "country",
    "transport",
    "output_unit",
    "process",
    "flow",
]


class PtxData:
    def __init__(self, data_dir=DATA_DIR):
        self.dimensions = {
            dim: _load_data(data_dir, name=f"dim_{dim}")
            for dim in ["country", "flow", "parameter", "process", "region"]
        }
        self.flh = _load_data(data_dir, name="flh").set_index("key").replace(np.nan, "")
        self.storage_cost_factor = (
            _load_data(data_dir, name="storage_cost_factor")
            .set_index("key")
            .replace(np.nan, "")
        )
        self.chains = (
            _load_data(data_dir, name="chains").set_index("chain").replace(np.nan, "")
        )
        self.scenario_data = {
            f"{year} ({parameter_range})": _load_data(
                data_dir, name=f"{year}_{parameter_range}"
            )
            .set_index("key")
            .replace(np.nan, "")
            for year, parameter_range in product(
                [2030, 2040], ["low", "medium", "high"]
            )
        }

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
            user data that overrides scenario data. DataFrame needs the columns
            ["source_region_code", "process_code", "parameter_code",  "value"]

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        self.check_valid_scenario_id(scenario)

        scenario_data = self.scenario_data[scenario].copy()

        if user_data is not None:
            scenario_data = self._update_scenario_data_with_user_data(
                scenario_data, user_data
            )

        if long_names:
            scenario_data = self._map_names_and_codes(
                scenario_data, mapping_direction="code_to_name"
            )

        return scenario_data

    def get_dimensions_parameter_code(
        self,
        dimension: Literal[
            "res_gen", "secproc_co2", "secproc_water", "region", "country"
        ],
        parameter_name: str,
    ) -> str:
        """
        Get the internal code for a paremeter within a certain dimension.

        Used to translate long name parameters from frontend to codes.

        Parameters
        ----------
        dimension : str
        parameter_name : str

        Returns
        -------
        str
        """
        # mapping of different parameter dimension names depending on "dimension"
        dimension_parameter_mapping = {
            "res_gen": "process",
            "secproc_co2": "process",
            "secproc_water": "process",
            "region": "region",
            "country": "country",
        }
        target_dim_name = dimension_parameter_mapping.get(dimension)
        df = self.get_dimension(dimension)
        return df.loc[
            df[target_dim_name + "_name"] == parameter_name, target_dim_name + "_code"
        ].iloc[0]

    def _map_names_and_codes(
        self,
        scenario_data: pd.DataFrame,
        mapping_direction: Literal["code_to_name", "name_to_code"],
    ):
        """
        Map codes in scenario data to long names and vice versa.

        Mapping is done for data points in the dimensions "parameter", "process",
        "flow", "region", and "country".

        Parameters
        ----------
        scenario_data : pd.DataFrame
        mapping_direction : str in {"code_to_name", "name_to_code"}


        Returns
        -------
        : pd.DataFrame
            Same size as input `scenario_data` but with replaced names/codes
            as a copy of the original data.

        Raises
        ------
        ValueError
            on invalid `mapping_direction` arguments
        """
        if mapping_direction not in ["code_to_name", "name_to_code"]:
            raise ValueError(
                "mapping direction needs to be 'name_to_code' or 'code_to_name'"
            )
        in_type = mapping_direction.split("_")[0]
        out_type = mapping_direction.split("_")[-1]

        for dim in ["parameter", "process", "flow", "region", "country"]:
            mapping = pd.Series(
                self.dimensions[dim][f"{dim}_{out_type}"].to_list(),
                index=self.dimensions[dim][f"{dim}_{in_type}"],
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
        return scenario_data

    def _update_scenario_data_with_user_data(
        self, scenario_data: pd.DataFrame, user_data: pd.DataFrame
    ):
        """
        Update scenario_data with custom user_data.

        Parameters
        ----------
        scenario_data : pd.DataFrame
            the (unmodfied) scenario data
        user_data : pd.DataFrame
            user data containing only rows of scenario_data that have been modified.
            The ids in the received user data from frontend are long names and need to
            be mapped to codes first.
        """
        user_data = user_data.copy().fillna("")
        scenario_data = scenario_data.copy()
        # user data from frontend only has columns
        # "source_region_code", "process_code", "value" and "parameter_code"
        for missing_dim in ["flow_code", "target_country_code"]:
            user_data[missing_dim] = ""

        # user data comes with long names from frontend
        user_data = self._map_names_and_codes(
            user_data, mapping_direction="name_to_code"
        )

        # we only can user DataFrame.update with matching index values
        # but we do not want tu use "key"
        for row in user_data.itertuples():
            selector = (
                (scenario_data["parameter_code"] == row.parameter_code)
                & (scenario_data["process_code"] == row.process_code)
                & (scenario_data["flow_code"] == row.flow_code)
                & (scenario_data["source_region_code"] == row.source_region_code)
                & (scenario_data["target_country_code"] == row.target_country_code)
            )
            if len(scenario_data.loc[selector]) == 0:
                raise ValueError(
                    f"could not replace user_parameterin scenario_data\n{row}"
                )
            scenario_data.loc[selector, "value"] = row.value
        return scenario_data

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
                - 'process'
                - 'flow'

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
            "process": self._get_process_dimension,
            "flow": self._get_flow_dimension,
            "parameter": self._get_parameter_dimension,
        }
        return _dimensions[dim]()

    def _get_process_dimension(self) -> pd.DataFrame:
        """Availible items for this class."""
        return self.dimensions["process"].set_index("process_code", drop=False)

    def _get_flow_dimension(self) -> pd.DataFrame:
        """Availible items for this class."""
        return self.dimensions["flow"].set_index("flow_code", drop=False)

    def _get_parameter_dimension(self) -> pd.DataFrame:
        """Availible items for this class."""
        return self.dimensions["parameter"].set_index("parameter_code", drop=False)

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

    def check_valid_scenario_id(self, scenario):
        """Check if a scenario key is valid."""
        if scenario not in self.scenario_data.keys():
            raise ValueError(
                f"No valid data scenario '{scenario}'. Possible values "
                f"are\n{list(self.scenario_data.keys())}"
            )


class DataHandler:
    """
    Handler class for parameter retrieval.

    Instances of this class can be used to retrieve data from a single scenario and
    combine it with set user data.
    """

    def __init__(
        self,
        ptxdata: PtxData,
        scenario: ScenarioCode,
        user_data: None | pd.DataFrame = None,
    ):
        ptxdata.check_valid_scenario_id(scenario)
        self.scenario = scenario
        self.user_data = user_data
        self.scenario_data = ptxdata.get_input_data(
            scenario, long_names=False, user_data=user_data
        )
        self.ptxdata = ptxdata

    def get_input_data(self, long_names):
        """Return scenario data.

        If user data is defined, specified values will be replaced with those.

        Parameters
        ----------
        long_names : bool, optional
            if True, will replace the codes used internally with long names that are
            used in the frontend.

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        return self.ptxdata.get_input_data(
            scenario=self.scenario,
            long_names=long_names,
            user_data=self.user_data,
        )

    def get_parameter_value(
        self,
        parameter_code: ParameterCode,
        process_code: str = None,
        flow_code: str = None,
        source_region_code: str = None,
        target_country_code: str = None,
        process_code_res: str = None,
        process_code_ely: str = None,
        process_code_deriv: str = None,
    ) -> float:
        """
        Get a parameter value for a process.

        Parameters
        ----------
        parameter_code : ParameterCode
            parameter category. Must be one of:
                - 'CALOR',
                - 'CAPEX'
                - 'CAP-T'
                - 'CONV'
                - 'DST-S-C'
                - 'DST-S-D'
                - 'DST-S-DP'
                - 'EFF'
                - 'FLH'
                - 'LIFETIME'
                - 'LOSS-T'
                - 'OPEX-F'
                - 'OPEX-T'
                - 'RE-POT'
                - 'SEASHARE'
                - 'SPECCOST'
                - 'WACC'
        process_code : str, optional
            Code for the process, by default None. Must be set for the following
            parameters:
                - CAPEX
                - CONV
                - EFF
                - FLH
                - LIFETIME
                - LOSS-T
                - OPEX-F
                - OPEX-T
                - RE-POT
                - WACC
        flow_code : str, optional
            Code for the flow, by default None. Must be set for the following
            parameters:
                - CALOR
                - CONV
                - SPECCOST
        source_region_code : str, optional
            Code for the source region, by default None. Must be set for the
            following parameters:
                - CAPEX
                - CAP-T
                - DST-S-C
                - DST-S-D
                - DST-S-DP
                - FLH
                - OPEX-F
                - RE-POT
                - SEASHARE
                - SPECCOST
                - WACC
        target_country_code : str, optional
            Code for the target country, by default None. Must be set for the
            following parameters:
                - CAP-T
                - DST-S-D
                - DST-S-DP
                - SEASHARE
        process_code_res : str, optional
            Code for the process_code_res, by default None. Must be set for the
            following parameters:
                - FLH
        process_code_ely : str, optional
            Code for the process_code_ely, by default None. Must be set for the
            following parameters:
                - FLH
        process_code_deriv : str, optional
            Code for the process_code_deriv, by default None. Must be set for the
            following parameters:
                - FLH

        Returns
        -------
        float
            the parameter value

        Raises
        ------
        ValueError
            if multiple values are found for a parameter combination.
        ValueError
            if no value is found for a parameter combination.
        """
        # convert missing codes tom empty strings
        # for data matching
        process_code = process_code or ""
        flow_code = flow_code or ""
        source_region_code = source_region_code or ""
        target_country_code = target_country_code or ""
        process_code_res = process_code_res or ""
        process_code_ely = process_code_ely or ""
        process_code_deriv = process_code_deriv or ""

        self._check_required_parameter_value_kwargs(
            parameter_code,
            process_code=process_code,
            flow_code=flow_code,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            process_code_res=process_code_res,
            process_code_ely=process_code_ely,
            process_code_deriv=process_code_deriv,
        )

        if (
            parameter_code == "FLH"
            and process_code
            not in self.ptxdata.get_dimension("res_gen")["process_code"].to_list()
        ):
            # FLH not changed by user_data
            df = self.ptxdata.flh
            selector = (
                (df["region"] == source_region_code)
                & (df["process_res"] == process_code_res)
                & (df["process_ely"] == process_code_ely)
                & (df["process_deriv"] == process_code_deriv)
                & (df["process_flh"] == process_code)
            )
        elif parameter_code == "STR-CF":
            # Storage cost factor not changedbyuser (and currently in separate file)
            df = self.ptxdata.storage_cost_factor
            selector = (
                (df["process_res"] == process_code_res)
                & (df["process_ely"] == process_code_ely)
                & (df["process_deriv"] == process_code_deriv)
            )
        else:
            df = self.scenario_data
            selector = self._construct_selector(
                df,
                parameter_code,
                process_code,
                flow_code,
                source_region_code,
                target_country_code,
            )

        row = df[selector]

        if len(row) == 0 and PARAMETER_DIMENSIONS[parameter_code]["global_default"]:
            # make query with empty "source_region_code"
            logger.debug("searching global default")
            selector = self._construct_selector(
                df,
                parameter_code=parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                source_region_code="",
                target_country_code=target_country_code,
            )
            row = df[selector]

        if len(row) > 1:
            raise ValueError("found more than one parameter value")
        elif len(row) == 0:
            raise ValueError(
                f"""did not find a parameter value for:
                parameter_code={parameter_code},
                process_code={process_code},
                flow_code={flow_code},
                source_region_code={source_region_code},
                target_country_code={target_country_code},
                process_code_res={process_code_res},
                process_code_ely={process_code_ely},
                process_code_deriv={process_code_deriv},
            """
            )
        return row.squeeze().at["value"]

    def _construct_selector(
        self,
        df: pd.DataFrame,
        parameter_code: ParameterCode,
        process_code: str,
        flow_code: str,
        source_region_code: str,
        target_country_code: str,
    ) -> pd.Series:
        """
        Create a boolean index object which can be used to filter df.

        Parameters
        ----------
        df : pd.DataFrame
            needs to have columns "parameter_code", "process_code", "flow_code",
            "source_region_code", and "target_country_code"
        """
        kwargs = {
            "process_code": process_code or "",
            "flow_code": flow_code or "",
            "source_region_code": source_region_code or "",
            "target_country_code": target_country_code or "",
        }
        selector = df["parameter_code"] == parameter_code
        for param in PARAMETER_DIMENSIONS[parameter_code]["required"]:
            selector &= df[param] == kwargs[param]

        return selector

    def _check_required_parameter_value_kwargs(
        self,
        parameter_code: ParameterCode,
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
            if not required_value:
                raise ValueError(
                    f"'{parameter_code}': the following parameters must be "
                    f"defined\n{required_param_names}\n"
                    f"Got: {kwargs}"
                )

    def get_dimension(self, dim: str) -> pd.DataFrame:
        """Delegate get_dimension to underlying data class."""
        return self.ptxdata.get_dimension(dim=dim)
