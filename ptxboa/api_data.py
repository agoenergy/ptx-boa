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
    df = pd.read_csv(
        filepath,
        # need to define custom na values due to Alpha2 code of Namibia
        na_values={
            "N/A",
            "n/a",
            "NULL",
            "null",
            "NaN",
            "-NaN",
            "nan",
            "-nan",
            "",
            "None",
        },
        keep_default_na=False,
    ).drop(columns="key", errors="ignore")
    # numerical columns should never be empty, dimension columns
    # maybe empty and will be filled with ""
    df = df.fillna("")
    return df


DATA_DIR = Path(__file__).parent.resolve() / "data"


def get_transport_distances(
    source_region_code,
    target_country_code,
    use_ship,
    ship_own_fuel,
    dist_ship,
    dist_pipeline,
    seashare_pipeline,
    existing_pipeline_cap,
):
    # TODO: new calculation of distances
    dist_transp = {}
    if source_region_code == target_country_code:
        # no transport (only China)
        pass
    elif dist_pipeline and not use_ship:
        # use pipeline if pipeline possible and ship not selected
        if existing_pipeline_cap:
            # use retrofitting
            dist_transp["PPLX"] = dist_pipeline * seashare_pipeline
            dist_transp["PPLR"] = dist_pipeline * (1 - seashare_pipeline)
        else:
            dist_transp["PPLS"] = dist_pipeline * seashare_pipeline
            dist_transp["PPL"] = dist_pipeline * (1 - seashare_pipeline)
    else:
        # use ship
        if ship_own_fuel:
            dist_transp["SHP-OWN"] = dist_ship
        else:
            dist_transp["SHP"] = dist_ship

    return dist_transp


def filter_chain_processes(chain, transport_distances):
    result_main = []
    result_transport = []
    for process_step in ["RES", "ELY", "DERIV"]:
        process_code = chain[process_step]
        if process_code:
            result_main.append(process_step)
    is_shipping = transport_distances.get("SHP") or transport_distances.get("SHP-OWN")
    is_pipeline = (
        transport_distances.get("PPLS")
        or transport_distances.get("PPL")
        or transport_distances.get("PPLX")
        or transport_distances.get("PPLR")
    )
    if is_shipping:
        if chain["PRE_SHP"]:  # not all have preprocessing
            result_transport.append("PRE_SHP")
    elif is_pipeline:
        if chain["PRE_PPL"]:  # not all have preprocessing
            result_transport.append("PRE_PPL")

    for k, v in transport_distances.items():
        if v:
            assert chain[k]
            result_transport.append(k)

    if is_shipping:
        if chain["POST_SHP"]:  # not all have preprocessing
            result_transport.append("POST_SHP")
    elif is_pipeline:
        if chain["POST_PPL"]:  # not all have preprocessing
            result_transport.append("POST_PPL")

    # TODO: CHECK that flow chain is correct

    return result_main, result_transport


ParameterCode = Literal[
    "CALOR",
    "CAPEX",
    "CAP-T",
    "CONV",
    "DST-S-D",
    "DST-S-DP",
    "EFF",
    "FLH",
    "LIFETIME",
    "LOSS-T",
    "OPEX-F",
    "OPEX-T",
    "OPEX-O",
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
        self.flh = self._load_flh_data(data_dir)
        self.storage_cost_factor = self._load_storage_cost_factor_data(data_dir)
        self.chains = (
            _load_data(data_dir, name="chains").set_index("chain").replace(np.nan, "")
        )
        self.scenario_data = {
            f"{year} ({parameter_range})": self._load_scenario_table(
                data_dir, f"{year}_{parameter_range}"
            )
            for year, parameter_range in product(
                [2030, 2040], ["low", "medium", "high"]
            )
        }

        # ----------------------------------------------------------------------------
        # loading parameters
        # ----------------------------------------------------------------------------

        self.PARAMETER_DIMENSIONS = {}
        # create class instances for parameters
        df_parameters = _load_data(data_dir, name="dim_parameter").set_index(
            "parameter_code", drop=False
        )
        assert set(df_parameters.index) == set(ParameterCode.__args__), set(
            ParameterCode.__args__
        ) - set(df_parameters.index)

        for parameter_code, specs in df_parameters.iterrows():
            required = [
                y
                for x, y in [
                    ("per_flow", "flow_code"),
                    ("per_process", "process_code"),
                    ("per_region", "source_region_code"),
                    ("per_import_country", "target_country_code"),
                ]
                if specs[x]
            ]
            global_default = specs["has_global_default"]

            if global_default:
                assert "source_region_code" in required
            self.PARAMETER_DIMENSIONS[parameter_code] = {
                "global_default": global_default,
                "required": required,
            }

    def _load_scenario_table(
        self, data_dir: str | Path, scenario: ScenarioCode
    ) -> pd.DataFrame:
        df = _load_data(data_dir, scenario).replace(np.nan, "")
        return self._assign_key_index(df, table_type="scenario")

    def _load_flh_data(self, data_dir: str | Path) -> pd.DataFrame:
        df = _load_data(data_dir, name="flh").replace(np.nan, "")
        return self._assign_key_index(df, table_type="flh")

    def _load_storage_cost_factor_data(self, data_dir: str | Path) -> pd.DataFrame:
        df = _load_data(data_dir, name="storage_cost_factor").replace(np.nan, "")
        return self._assign_key_index(df, table_type="storage_cost_factor")

    def _assign_key_index(
        self,
        df: pd.DataFrame,
        table_type: Literal["flh", "scenario", "storage_cost_factor"],
    ) -> pd.DataFrame:
        """
        Assing a unique index to a dataframe containing "index" columns.

        Parameters
        ----------
        df : pd.DataFrame
        table_type : str in {"flh", "scenario", "storage_cost_factor"}

        Returns
        -------
        pd.DataFrame

        Raises
        ------
        ValueError
            if the constructed index is not unique
        """
        keys_in_table = {
            "flh": [
                "region",
                "process_res",
                "process_ely",
                "process_deriv",
                "process_flh",
            ],
            "scenario": [
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
            ],
            "storage_cost_factor": ["process_res", "process_ely", "process_deriv"],
        }
        key_columns = keys_in_table[table_type]
        df[key_columns] = df[key_columns].astype(str)
        df["key"] = df[key_columns].agg("-".join, axis=1)
        if not df["key"].is_unique:
            raise ValueError(f"duplicate keys in storage {table_type} data.")
        return df.set_index("key")

    def get_input_data(
        self,
        scenario: ScenarioCode,
        long_names: bool = True,
        user_data: dict = None,
        enforce_copy: bool = True,
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
            "source_region_code", "process_code", "parameter_code", "flow_code", and
            "value".
        enforce_copy: bool
            Will always return a copy of the user data when true, when false, only
            returns a copy when user data is not None. When enforce_copy is False and
            no user data is given, a view will be returned.

        Returns
        -------
        : pd.DataFrame
            columns are 'parameter_code', 'process_code', 'flow_code',
            'source_region_code', 'target_country_code', 'value', 'unit', 'source'

        """
        self.check_valid_scenario_id(scenario)

        if enforce_copy or user_data is not None:
            scenario_data = self.scenario_data[scenario].copy()
        else:
            scenario_data = self.scenario_data[scenario]

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
        if not parameter_name or parameter_name == "Specific costs":
            return ""

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
        # "source_region_code", "process_code", "value" and "parameter_code", and
        # "flow_code" we need to replace missing column "target_country_code"
        user_data["target_country_code"] = ""

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
            scenario,
            long_names=False,
            user_data=user_data,
            enforce_copy=False,
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
            enforce_copy=True,
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
        default: float = None,
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

        default : float, optional
            if no data is found, this value is returned.
            if no data is found and default is not specified, a ValueError is raised.

        Returns
        -------
        float
            the parameter value

        Raises
        ------
        ValueError
            if multiple values are found for a parameter combination.
        ValueError
            if no value is found for a parameter combination and no default is given.
        """
        # convert missing codes tom empty strings
        # for data matching
        params = {
            "parameter_code": parameter_code,
            "process_code": process_code or "",
            "flow_code": flow_code or "",
            "source_region_code": source_region_code or "",
            "target_country_code": target_country_code or "",
            "process_code_res": process_code_res or "",
            "process_code_ely": process_code_ely or "",
            "process_code_deriv": process_code_deriv or "",
        }

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
            key = "-".join(
                [
                    params[k]
                    for k in [
                        "source_region_code",
                        "process_code_res",
                        "process_code_ely",
                        "process_code_deriv",
                        "process_code",
                    ]
                ]
            )
        elif parameter_code == "STR-CF":
            # Storage cost factor not changed by user (and currently in separate file)
            df = self.ptxdata.storage_cost_factor
            key = "-".join(
                [
                    params[k]
                    for k in [
                        "process_code_res",
                        "process_code_ely",
                        "process_code_deriv",
                    ]
                ]
            )
        else:
            df = self.scenario_data
            key = self._construct_key_in_scenario_data(params)

        try:
            row = df.at[key, "value"]
            empty_result = False
        except KeyError:
            empty_result = True
        if (
            empty_result
            and self.ptxdata.PARAMETER_DIMENSIONS[parameter_code]["global_default"]
        ):
            # make query with empty "source_region_code"
            logger.debug(
                f"searching global default, did not find entry for key '{key}'"
            )
            params["source_region_code"] = ""
            params["target_country_code"] = ""
            key = self._construct_key_in_scenario_data(params)
            try:
                row = df.at[key, "value"]
                empty_result = False
            except KeyError:
                empty_result = True

        if empty_result:
            if default is not None:
                return default
            raise ValueError(
                f"""did not find a parameter value for key '{key}':
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
        return row

    def _construct_key_in_scenario_data(
        self,
        params: dict,
    ) -> pd.Series:
        """
        Create a boolean index object which can be used to filter df.

        Parameters
        ----------
        params : dict
            dictionary which needs to contain the following keys:
            ["parameter_code", "process_code", "flow_code", "source_region_code",
            "target_country_code"]
        """
        selector = params["parameter_code"]
        for k in [
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ]:
            if (
                k
                in self.ptxdata.PARAMETER_DIMENSIONS[params["parameter_code"]][
                    "required"
                ]
            ):
                selector += f"-{params[k]}"
            else:
                selector += "-"
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
        required_param_names = self.ptxdata.PARAMETER_DIMENSIONS[parameter_code][
            "required"
        ]

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

    def get_calculation_data(
        self,
        secondary_processes: dict,
        chain: dict,
        process_code_res: str,
        process_code_ely: str,
        process_code_deriv: str,
        source_region_code: str,
        target_country_code: str,
        use_ship: bool,
        ship_own_fuel: bool,
    ) -> pd.DataFrame:
        """Calculate results."""
        result = {
            "main_process_chain": [],
            "transport_process_chain": [],
            "secondary_process": {},
            "secondary_flow": {},
            "parameter": {},
        }

        # get process codes for selected chain
        df_processes = self.get_dimension("process")
        df_flows = self.get_dimension("flow")

        def get_parameter_value_w_default(
            parameter_code, process_code="", flow_code="", default=None
        ):
            return self.get_parameter_value(
                parameter_code=parameter_code,
                process_code=process_code,
                flow_code=flow_code,
                source_region_code=source_region_code,
                target_country_code=target_country_code,
                process_code_res=process_code_res,
                process_code_ely=process_code_ely,
                process_code_deriv=process_code_deriv,
                default=default,
            )

        def flow_conv_params(process_code):
            result = {}
            flows = df_processes.loc[process_code, "secondary_flows"].split("/")
            flows = [x.strip() for x in flows if x.strip()]
            for flow_code in flows:
                result[flow_code] = get_parameter_value_w_default(
                    parameter_code="CONV",
                    process_code=process_code,
                    flow_code=flow_code,
                    default=0,
                )
            return result

        def get_process_params(process_code):
            result = {}
            result["EFF"] = get_parameter_value_w_default(
                "EFF", process_code=process_code, default=1
            )
            result["FLH"] = get_parameter_value_w_default(
                "FLH", process_code=process_code, default=7000  # TODO: default?
            )
            result["LIFETIME"] = get_parameter_value_w_default(
                "LIFETIME", process_code=process_code, default=20  # TODO: default?
            )
            result["CAPEX"] = get_parameter_value_w_default(
                "CAPEX", process_code=process_code, default=0
            )  # TODO
            result["OPEX-F"] = get_parameter_value_w_default(
                "OPEX-F", process_code=process_code, default=0
            )
            result["OPEX-O"] = get_parameter_value_w_default(
                "OPEX-O", process_code=process_code, default=0
            )
            result["CONV"] = flow_conv_params(process_code)

        def get_transport_process_params(process_code, dist_transport):
            result = {}
            # TODO: also save in results
            loss_t = get_parameter_value_w_default(
                "LOSS-T", process_code=process_code, default=0
            )
            result["EFF"] = 1 - loss_t * dist_transport
            result["OPEX-T"] = get_parameter_value_w_default(
                "OPEX-T", process_code=process_code, default=0
            )
            result["OPEX-O"] = get_parameter_value_w_default(
                "OPEX-O", process_code=process_code, default=0
            )
            result["CONV"] = flow_conv_params(process_code)
            return result

        def get_flow_params():
            # TODO: only get used flows?
            secondary_flows = list(
                df_flows.loc[df_flows["secondary_flow"], "flow_code"]
            )
            result = {}
            for flow_code in secondary_flows:
                result[flow_code] = get_parameter_value_w_default(
                    "SPECCOST", flow_code=flow_code
                )
            return result

        # some flows are grouped into their own output category (but not all)
        # so we load the mapping from the data

        # iterate over main chain, update the value in the main flow
        # and accumulate result data from each process

        # get general parameters

        result["parameter"]["WACC"] = get_parameter_value_w_default("WACC")
        result["parameter"]["STR-CF"] = get_parameter_value_w_default("STR-CF")
        result["parameter"]["CALOR"] = get_parameter_value_w_default(
            parameter_code="CALOR", flow_code=chain["FLOW_OUT"]
        )

        # get transport distances and options
        # TODO? add these also to data
        dist_pipeline = get_parameter_value_w_default("DST-S-DP", default=0)
        seashare_pipeline = get_parameter_value_w_default("SEASHARE", default=0)
        existing_pipeline_cap = get_parameter_value_w_default("CAP-T", default=0)
        dist_ship = get_parameter_value_w_default("DST-S-D", default=0)

        if not use_ship and not chain["CAN_PIPELINE"]:
            logging.warning("Must use ship")
            use_ship = True

        transport_distances = get_transport_distances(
            source_region_code,
            target_country_code,
            use_ship,
            ship_own_fuel,
            dist_ship,
            dist_pipeline,
            seashare_pipeline,
            existing_pipeline_cap,
        )

        chain["RES"] = process_code_res

        chain_steps_main, chain_steps_transport = filter_chain_processes(
            chain, transport_distances
        )

        for process_step in chain_steps_main:
            process_code = chain[process_step]
            get_process_params(process_code)

        for _, process_code in secondary_processes.items():
            if not process_code:
                continue
            get_process_params(process_code)

        for process_step in chain_steps_transport:
            process_code = chain[process_step]
            if not process_code:
                raise Exception((process_step, chain))
            if process_step in transport_distances:
                dist_transport = transport_distances[process_step]
                get_transport_process_params(process_code, dist_transport)
            else:  # pre/post
                get_process_params(process_code)

        result["parameter"]["SPECCOST"] = get_flow_params()

        return result
