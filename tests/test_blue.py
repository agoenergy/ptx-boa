"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static._type_defs import ChainDef
from tests.test_api import ptxdata_dir_static
from tests.utils import assert_deep_equal_approx


def _translate_user_data(user_data: pd.DataFrame) -> None:
    # NOTE: the columns say *_code,
    # but user data actually must be passed as names
    for colname in user_data.columns:
        if colname.endswith("_code"):
            user_data[colname] = user_data[colname].fillna("")

    for idx, row in user_data.iterrows():
        for colname, value in row.items():
            colname = str(colname)
            if value and colname.endswith("_code"):
                dimname = colname.replace("_code", "")
                basename = dimname.replace("target_", "").replace("source_", "")
                dim = DataHandler.dimensions[dimname]  # type: ignore
                try:
                    value = dim.loc[value, basename + "_name"]
                except Exception:
                    raise KeyError(
                        f"{colname}={value} not in {dimname}: "
                        f"{sorted(dim.index)}, {sorted(dim.columns)}"
                    )
                user_data.loc[idx, colname] = value  # type: ignore


# @pytest.mark.skip # noqa
@pytest.mark.parametrize(
    "scenario, kwargs, api_kwargs",
    [
        [
            "2040 (medium)",
            {
                "chain_name": "Blue Iron (blue)*",
                "source_region_code": "QAT",
                "target_country_code": "DEU",
                "process_res": None,
                "secondary_processes": {},
                "ship_own_fuel": False,
                "transport": "Ship",
            },
            {
                "region": "Qatar",
                "country": "Germany",
                "chain": "Blue Iron (blue)*",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
        ],
    ],
)
def test_new_blue_chain_fixed_data(scenario, kwargs, api_kwargs):
    """Data test for blue iron chain using test data."""
    user_data = pd.DataFrame(
        [
            {
                "parameter_code": "CAPEX",
                "process_code": "EAF#B",
                "value": 0.417344,
            },
            {
                "parameter_code": "OPEX-F",
                "process_code": "EAF#B",
                "value": 0.01252,
            },
            {
                "parameter_code": "OPEX-O",
                "process_code": "EAF#B",
                "value": 0.183679,
            },
            {
                "parameter_code": "CAPEX",
                "process_code": "NG-DRI-C#B",
                "value": 0.591876,
            },
            {
                "parameter_code": "OPEX-F",
                "process_code": "NG-DRI-C#B",
                "value": 0.017756,
            },
            {
                "source_region_code": "QAT",
                "parameter_code": "WACC",
                "value": 0,
            },
            {
                "source_region_code": "QAT",
                "target_country_code": "DEU",
                "parameter_code": "DST-S-D",
                "value": 999,
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "SPECCOST",
                "value": 0,
            },
            {
                "flow_code": "IOP-S",
                "parameter_code": "SPECCOST",
                "value": 0,
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "NG-G",  # main flow in
                "parameter_code": "LOSS",
                "value": 0.05,  # process_calc!E9
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "EFF",
                "value": 0.336004,  # process_calc!E3
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.476859,  # process_calc!E4
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "IOP-S",
                "parameter_code": "CONV",
                "value": 1.373737,  # process_calc!E6
            },
            {
                "process_code": "EAF#B",
                "parameter_code": "LOSS",
                "flow_code": "NG-G",
                "value": 0.05,  # process_calc!J9
            },
            {
                "process_code": "EAF#B",
                "parameter_code": "EFF",
                "value": 1.010101,  # process_calc!J3
            },
            {
                "process_code": "EAF#B",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.651000,  # process_calc!J6
            },
            {
                "process_code": "EAF#B",
                "flow_code": "NG-G",
                "parameter_code": "CONV",
                "value": 0.004,  # process_calc!J4
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-S",
                "flow_code": "NG-G",
                "value": 0.45,  # process_calc!E11
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-S",
                "flow_code": "CH4-G",
                "value": 0.45,  # process_calc!E11
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-R",
                "flow_code": "NG-G",
                "value": 0.9,  # process_calc!E14
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-R",
                "flow_code": "CH4-G",
                "value": 0.9,  # process_calc!E14
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CBOUND",
                "process_code": "NG-DRI-C#B",
                "value": 0.040812,  # process_calc!E17
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CH4SHARE",
                "value": 0.909,  # process_calc!E20
            },
            {
                "flow_code": "STL-S",
                "parameter_code": "CBOUND",
                "process_code": "EAF#B",
                "value": 0.00396,  # process_calc!J17
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "NG-G",
                "value": 201,  # emission_factors!D7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "CH4-G",
                "value": 201,  # emission_factors!I7
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "NG-G",
                "source_region_code": "QAT",
                "value": 201,  # emission_factors!D9
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "CH4-G",
                "value": 201,
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "EL",
                "source_region_code": "QAT",
                "value": 402,  # emission_factors!E9
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "EL",
                "source_region_code": "DEU",
                "value": 300,  # emission_factors!F9
            },
        ]
    )

    _translate_user_data(user_data)

    pprint(user_data)

    # FIXME: this is a test chain and not (yet) marked as "blue" in data
    # so we need to fix it manually
    DataHandler.get_dimension("chain").loc["Blue Iron (blue)*", "is_blue"] = "True"

    data_handler = DataHandler(
        data_dir=ptxdata_dir_static,
        scenario=scenario,
        user_data=user_data,
        tool_version_color="blue",
    )

    chain_def = ChainDef(**kwargs)
    ptx_calc = PtxCalc.get_or_create(chain_def)

    data = data_handler.get_calculation_data(
        ptx_calc=ptx_calc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=False,
    )
    ptxcalc_results = ptx_calc.calculate(data=data)

    # test api output
    api = PtxboaAPI(data_dir=ptxdata_dir_static)
    api_result = api.calculate(  # noqa
        scenario=scenario,
        **api_kwargs,
        user_data=user_data,
        tool_version_color="blue",
        optimize_flh=False,
        output_unit="USD/t",  # must be per ton for steel
    )
    res_emission_mass = api_result.emission_mass[  # type: ignore
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")
    res_emission = api_result.emissions[  # type: ignore
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")

    # round and sort for easier comparison
    values = ptxcalc_results.results_flows_chain

    expected = {
        "calculation_data": {
            "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
            "main_export_process_chain": [
                {
                    "CAPEX": 0.591876,
                    "CBOUND": {"NG-G": 0.040812},
                    "CH4SHARE": {"NG-G": 0.909},
                    "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                    "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                    "CONV": {"EL": 0.476859, "IOP-S": 1.373737},
                    "EFF": 0.32000381,
                    "EF_E": {"CH4-G": 201.0, "EL": 402.0, "NG-G": 201.0},
                    "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                    "FLH": 7000,
                    "LIFETIME": 20,
                    "LOSS": {"NG-G": 0.05},
                    "OPEX-F": 0.017756,
                    "process_code": "NG-DRI-C#B",
                    "step": "DERIV",
                },
                {
                    "CH4SHARE": {"NG-G": 0.909},
                    "EFF": 1.0,
                    "EF_E": {"NG-G": 201.0},
                    "EF_M": {"NG-G": 201.0},
                    "FLH": 7000,
                    "LIFETIME": 20,
                    "process_code": "NG-PROD#B",
                    "step": "NG_PROD",
                },
            ],
            "main_import_process_chain": [
                {
                    "CAPEX": 0.417344,
                    "CH4SHARE": {"NG-G": 0.909},
                    "CONV": {"EL": 0.651, "NG-G": 0.0042},
                    "EFF": 1.010101,
                    "EF_E": {"EL": 300.0},
                    "EF_M": {"NG-G": 201.0},
                    "FLH": 7000,
                    "LIFETIME": 20,
                    "LOSS": {"NG-G": 0.05},
                    "OPEX-F": 0.01252,
                    "OPEX-O": 0.183679,
                    "process_code": "EAF#B",
                    "step": "DERIV_I",
                }
            ],
            "main_transport_process_chain": [
                {
                    "DIST": 999.0,
                    "DST-S-D": 999.0,
                    "EFF": 1.0,
                    "process_code": "DRI-SB#B",
                    "step": "SHP",
                }
            ],
            "parameter": {
                "SPECCOST": {
                    "CO2-G": 0.04451862,
                    "EL": 0.08078,
                    "H2O-L": 0.0013738,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                }
            },
            "parameter_import": {
                "SPECCOST": {
                    "CO2-G": 0.04451862,
                    "EL": 0.08078,
                    "H2O-L": 0.0013738,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                }
            },
        },
        "flow_values": [
            {
                "main_flow_in": 3.0937132,
                "main_flow_out": 0.99000001,
                "process_code": "NG-DRI-C#B",
                "secondary_flows_in": {"EL": 0.47209041, "IOP-S": 1.35999964},
                "step": "DERIV",
            },
            {
                "main_flow_in": 0.99000001,
                "main_flow_out": 1,
                "process_code": "EAF#B",
                "secondary_flows_in": {"EL": 0.651, "NG-G": 0.0042},
                "step": "DERIV_I",
            },
            {
                "main_flow_out": 3.0937132,
                "process_code": "NG-PROD#B",
                "step": "NG_PROD",
            },
            {
                "main_flow_in": 0.99000001,
                "main_flow_out": 0.99000001,
                "process_code": "DRI-SB#B",
                "step": "SHP",
            },
        ],
        "res_emission": [
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "EAF#B",
                "values": 372.48820245,
            },
            {
                "emission_type": "indirect",
                "gas_type": "CO2",
                "process_subtype": "EAF#B",
                "values": 195300.0,
            },
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "NG-DRI-C#B",
                "values": 274374.2069403,
            },
            {
                "emission_type": "indirect",
                "gas_type": "CO2",
                "process_subtype": "NG-DRI-C#B",
                "values": 189780.3467178,
            },
        ],
        "res_emission_mass": [
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "EAF#B",
                "values": 372.48820245,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "EAF#B",
                "values": 804.0,
            },
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "NG-DRI-C#B",
                "values": 274374.2069403,
            },
        ],
    }
    actually = {
        "calculation_data": data,
        "flow_values": values,
        "res_emission": res_emission,
        "res_emission_mass": res_emission_mass,
    }

    assert_deep_equal_approx(expected, actually, sort_list_by_keys=["step"])


@pytest.mark.parametrize(
    "api_kwargs,expected",
    [
        # =============================================================================
        # CASE 1
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Qatar",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_supply",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "calculation_data": {
                    "context": {
                        "source_region_code": "QAT",
                        "target_country_code": "DEU",
                    },
                    "main_export_process_chain": [
                        {
                            "CAPEX": 0.59187636,
                            "CBOUND": {"NG-G": 0.04081161},
                            "CH4SHARE": {"NG-G": 0.909},
                            "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                            "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                            "CONV": {"EL": 0.47685859, "IOP-S": 1.37373737},
                            "EFF": 0.3360036,
                            "EF_E": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                            "EF_M": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 20.0,
                            "OPEX-F": 0.01775629,
                            "WACC": 0.0487,
                            "process_code": "NG-DRI-C#B",
                            "step": "DERIV",
                        },
                        {
                            "CBOUND": {"NG-G": 0.0548514},
                            "CH4SHARE": {"NG-G": 0.909},
                            "CONV": {"DIESEL-L": 0.00059456},
                            "EFF": 0.98270994,
                            "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "LOSS": {"NG-G": 0.00378},
                            "OPEX-O": 0.00486257,
                            "WACC": 0.0487,
                            "process_code": "NG-PROD#B",
                            "step": "NG_PROD",
                        },
                    ],
                    "main_import_process_chain": [
                        {
                            "CAPEX": 0.41734427,
                            "CBOUND": {"B-DRI-S": 0.004},
                            "CH4SHARE": {"NG-G": 0.92080641},
                            "CONV": {"EL": 0.651, "NG-G": 0.3},
                            "EFF": 1.01010101,
                            "EF_E": {"EL": 100.0, "NG-G": 201.0},
                            "EF_M": {"EL": 100.0, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 20.0,
                            "OPEX-F": 0.01252033,
                            "OPEX-O": 0.18367869,
                            "WACC": 0.0423,
                            "process_code": "EAF#B",
                            "step": "DERIV_I2",
                        }
                    ],
                    "main_transport_process_chain": [
                        {
                            "DIST": 12830.0,
                            "DST-S-D": 12830.0,
                            "DST-S-DP": 5000.0,
                            "EFF": 1.0,
                            "OPEX-T": 3.8e-07,
                            "process_code": "DRI-SB#B",
                            "step": "SHP",
                        }
                    ],
                    "parameter": {
                        "SPECCOST": {
                            "CO2-G": 0.04451862,
                            "DIESEL-L": 0.04285714,
                            "EL": 0.08078,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "IOP-S": 0.26707598,
                            "N2-G": 0.01154,
                        },
                        "WACC": 0.0487,
                    },
                    "parameter_import": {
                        "SPECCOST": {
                            "CO2-G": 0.04451862,
                            "DIESEL-L": 0.04285714,
                            "EL": 0.1,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "IOP-S": 0.26707598,
                            "N2-G": 0.01154,
                            "NG-G": 0.03056527,
                        },
                        "WACC": 0.0423,
                    },
                    "secondary_process": {
                        "CO2-C": {
                            "EFF": 0.95,
                            "EF_E": {"CO2-C": 1.0},
                            "EF_M": {"CO2-C": 1.0},
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "OPEX-O": 0.03024746,
                            "WACC": 0.0487,
                            "process_code": "CO2-T+S#B",
                        },
                        "EL": {
                            "CAPEX": 2408.19070902,
                            "CH4SHARE": {"NG-G": 0.909},
                            "CO2CPT-R": {"NG-G": 0.89777778},
                            "CO2CPT-S": {"NG-G": 1.0},
                            "EFF": 0.50491129,
                            "EF_E": {"CO2-C": 1.0, "NG-G": 201.0},
                            "EF_M": {"CO2-C": 1.0, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 30.0,
                            "OPEX-F": 63.75889534,
                            "WACC": 0.0487,
                            "process_code": "CCGT-CC#B",
                        },
                    },
                },
                "flow_values": [
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 0.99,
                        "process_code": "NG-DRI-C#B",
                        "secondary_flows_in": {"EL": 0.47209, "IOP-S": 1.36},
                        "step": "DERIV",
                    },
                    {
                        "main_flow_in": 0.99,
                        "main_flow_out": 1,
                        "process_code": "EAF#B",
                        "secondary_flows_in": {"EL": 0.651, "NG-G": 0.3},
                        "step": "DERIV_I2",
                    },
                    {
                        "main_flow_out": 3.88139293,
                        "process_code": "NG-PROD#B",
                        "secondary_flows_in": {"DIESEL-L": 0.00230771},
                        "step": "NG_PROD",
                    },
                    {"process_code": "CO2-T+S#B", "step": "SECONDARY:None"},
                    {
                        "main_flow_in": 0.93499593,
                        "main_flow_out": 0.47209,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:None",
                    },
                    {
                        "main_flow_in": 0.99,
                        "main_flow_out": 0.99,
                        "process_code": "DRI-SB#B",
                        "step": "SHP",
                    },
                ],
                "res_costs": [
                    {
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 0.25795454,
                    },
                    {
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 0.36323249,
                    },
                    {
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.01470907,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.01897244,
                    },
                    {
                        "process_subtype": "DRI-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00478268,
                    },
                ],
                "res_emission_mass": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "Bound in product",
                        "values": 4.0,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "values": 60296.0,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "values": 65100.0,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "values": 615.60521866,
                    },
                ],
            },
            # marks=pytest.mark.skip,  # noqa
        ),
        # =============================================================================
        # CASE 2
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Algeria",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_demand",  # sheet 41
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "calculation_data": {
                    "context": {
                        "source_region_code": "DZA",
                        "target_country_code": "DEU",
                    },
                    "main_export_process_chain": [
                        {
                            "CBOUND": {"NG-G": 0.0548514},
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "CONV": {"DIESEL-L": 0.00060236},
                            "EFF": 0.90362604,
                            "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "LOSS": {"NG-G": 0.0139},
                            "OPEX-O": 0.00316265,
                            "WACC": 0.14554836,
                            "process_code": "NG-PROD#B",
                            "step": "NG_PROD",
                        },
                        {
                            "CAPEX": 408.10708157,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "CONV": {"EL": 0.00274153},
                            "EFF": 0.85708919,
                            "EF_E": {"NG-G": 201.0},
                            "EF_M": {"NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 30.0,
                            "LOSS": {"NG-G": 0.0005},
                            "OPEX-F": 8.16214163,
                            "WACC": 0.14554836,
                            "process_code": "CH4-LIQ#B",
                            "step": "PRE_SHP",
                        },
                    ],
                    "main_import_process_chain": [
                        {
                            "CAPEX": 0.59187636,
                            "CBOUND": {"NG-G": 0.04081161},
                            "CH4SHARE": {"NG-G": 0.92080641},
                            "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                            "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                            "CONV": {"EL": 0.47685859, "IOP-S": 1.37373737},
                            "EFF": 0.3360036,
                            "EF_E": {
                                "CH4-G": 201.0,
                                "CO2-C": 1.0,
                                "EL": 100.0,
                                "NG-G": 201.0,
                            },
                            "EF_M": {
                                "CH4-G": 201.0,
                                "CO2-C": 1.0,
                                "EL": 100.0,
                                "NG-G": 201.0,
                            },
                            "FLH": 7000,
                            "LIFETIME": 20.0,
                            "OPEX-F": 0.01775629,
                            "WACC": 0.0423,
                            "process_code": "NG-DRI-C#B",
                            "step": "DERIV_I",
                        },
                        {
                            "CAPEX": 0.41734427,
                            "CBOUND": {"B-DRI-S": 0.004},
                            "CH4SHARE": {"NG-G": 0.92080641},
                            "CONV": {"EL": 0.651, "NG-G": 0.3},
                            "EFF": 1.01010101,
                            "EF_E": {"EL": 100.0, "NG-G": 201.0},
                            "EF_M": {"EL": 100.0, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 20.0,
                            "OPEX-F": 0.01252033,
                            "OPEX-O": 0.18367869,
                            "WACC": 0.0423,
                            "process_code": "EAF#B",
                            "step": "DERIV_I2",
                        },
                        {
                            "CH4SHARE": {"NG-G": 0.92080641},
                            "CONV": {"DIESEL-L": 2e-06, "EL": 0.00048, "NG-G": 0.00085},
                            "EFF": 1.0,
                            "EF_E": {
                                "DIESEL-L": 266.76,
                                "EL": 100.0,
                                "NG-G": 201.0,
                                "NG-L": 201.0,
                            },
                            "EF_M": {
                                "DIESEL-L": 266.76,
                                "EL": 100.0,
                                "NG-G": 201.0,
                                "NG-L": 201.0,
                            },
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "LOSS": {"NG-G": 4e-08},
                            "WACC": 0.0423,
                            "process_code": "CH4-RGAS#B",
                            "step": "POST_SHP",
                        },
                    ],
                    "main_transport_process_chain": [
                        {
                            "CONV": {"BFUEL-L": 0.01047548},
                            "CONV-OT": {"BFUEL-L": 3.3e-06},
                            "DIST": 3174.14,
                            "DST-S-D": 3174.14,
                            "DST-S-DP": 3000.0,
                            "EFF": 1.0,
                            "EF_E": {"NG-L": 201.0},
                            "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                            "SEASHARE": 0.1,
                            "process_code": "CH4-SB#B",
                            "step": "SHP",
                        }
                    ],
                    "parameter": {
                        "SPECCOST": {
                            "BFUEL-L": 0.00322434,
                            "CO2-G": 0.04451862,
                            "DIESEL-L": 0.04285714,
                            "EL": 0.08078,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "N2-G": 0.01154,
                        },
                        "WACC": 0.14554836,
                    },
                    "parameter_import": {
                        "SPECCOST": {
                            "BFUEL-L": 0.00322434,
                            "CO2-G": 0.04451862,
                            "DIESEL-L": 0.04285714,
                            "EL": 0.1,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "IOP-S": 0.26707598,
                            "N2-G": 0.01154,
                            "NG-G": 0.03056527,
                        },
                        "WACC": 0.0423,
                    },
                    "secondary_process": {
                        "CO2-C": {
                            "EFF": 0.95,
                            "EF_E": {"CO2-C": 1.0},
                            "EF_M": {"CO2-C": 1.0},
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "OPEX-O": 0.11656581,
                            "WACC": 0.14554836,
                            "process_code": "CO2-T+S#B",
                        },
                        "EL": {
                            "CAPEX": 2408.19070902,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "CO2CPT-R": {"NG-G": 0.89777778},
                            "CO2CPT-S": {"NG-G": 1.0},
                            "EFF": 0.50491129,
                            "EF_E": {"CO2-C": 1.0, "NG-G": 201.0},
                            "EF_M": {"CO2-C": 1.0, "NG-G": 201.0},
                            "FLH": 7000,
                            "LIFETIME": 30.0,
                            "OPEX-F": 63.75889534,
                            "WACC": 0.14554836,
                            "process_code": "CCGT-CC#B",
                        },
                    },
                    "secondary_process_import": {
                        "CO2-C": {
                            "EFF": 0.95,
                            "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                            "EF_M": {"CO2-C": 1.0, "EL": 100.0},
                            "FLH": 7000,
                            "LIFETIME": 20,
                            "OPEX-O": 0.14792048,
                            "WACC": 0.0423,
                            "process_code": "CO2-T+S#B",
                        }
                    },
                },
                "flow_values": [
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 0.99,
                        "process_code": "NG-DRI-C#B",
                        "secondary_flows_in": {"EL": 0.47209, "IOP-S": 1.36},
                        "step": "DERIV_I",
                    },
                    {
                        "main_flow_in": 0.99,
                        "main_flow_out": 1,
                        "process_code": "EAF#B",
                        "secondary_flows_in": {"EL": 0.651, "NG-G": 0.3},
                        "step": "DERIV_I2",
                    },
                    {
                        "main_flow_out": 3.45367654,
                        "process_code": "NG-PROD#B",
                        "secondary_flows_in": {"DIESEL-L": 0.00208037},
                        "step": "NG_PROD",
                    },
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-RGAS#B",
                        "secondary_flows_in": {
                            "DIESEL-L": 5.89e-06,
                            "EL": 0.00141427,
                            "NG-G": 0.00250444,
                        },
                        "step": "POST_SHP",
                    },
                    {
                        "main_flow_in": 3.43767842,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-LIQ#B",
                        "secondary_flows_in": {"EL": 0.00807763},
                        "step": "PRE_SHP",
                    },
                    {"process_code": "CO2-T+S#B", "step": "SECONDARY:None"},
                    {"process_code": "CO2-T+S#B", "step": "SECONDARY:None"},
                    {
                        "main_flow_in": 0.01599812,
                        "main_flow_out": 0.00807763,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:None",
                    },
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-SB#B",
                        "secondary_flows_in": {"BFUEL-L": 0.03086494},
                        "step": "SHP",
                    },
                ],
                "res_costs": [
                    {
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 0.25795454,
                    },
                    {
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 0.41044113,
                    },
                    {
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.00048502,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.01101191,
                    },
                    {
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.02886908,
                    },
                    {
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00021823,
                    },
                    {
                        "process_subtype": "CH4-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 9.952e-05,
                    },
                ],
                "res_emission_mass": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "Bound in product",
                        "values": 4.0,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-LIQ#B",
                        "values": 3166.31460453,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-RGAS#B",
                        "values": 0.000189,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "values": 504.96388918,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "values": 141.427056,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-SB#B",
                        "values": 9033.5494204,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "values": 60296.0,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "values": 65100.0,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "NG-DRI-C#B",
                        "values": 47209.0,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "values": 554.95967351,
                    },
                ],
            },
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data(api_kwargs, expected):
    """Data test for blue iron chain using current data."""
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    api_result = api.calculate(  # noqa
        **api_kwargs, tool_version_color="blue", optimize_flh=False, output_unit="USD/t"
    )

    calculation_data = api_result.todo_data
    values = api_result.todo_results_flows

    res_emission_mass = api_result.emission_mass[  # type: ignore
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")
    # round and sort for easier comparison

    res_costs = (
        api_result.todo_df_results_cost_unscaled[  # type: ignore
            ["process_subtype", "process_type", "values"]
        ]
        .groupby(["process_subtype", "process_type"])
        .sum()
        .reset_index()
        .to_dict(orient="records")
    )
    # round and sort for easier comparison

    actual = {
        "calculation_data": calculation_data,
        "flow_values": values,
        "res_emission_mass": res_emission_mass,
        "res_costs": res_costs,
    }
    assert_deep_equal_approx(
        expected,
        actual,
        allow_new_dict_items=True,
        sort_list_by_keys=[
            "step",
            "process_type",
            "process_subtype",
            "cost_type",
        ],
    )


@pytest.mark.parametrize(
    "api_kwargs,expected",
    [
        # =============================================================================
        # CASE 1
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Qatar",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_supply",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
                "parameter": {
                    "WACC": 0.0487,
                    "SPECCOST": {
                        "IOP-S": 0.26707598,
                        "DIESEL-L": 0.04285714,
                        "EL": 0.08078,
                        "CO2-G": 0.04451862,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "N2-G": 0.01154,
                    },
                },
                "parameter_import": {
                    "WACC": 0.0423,
                    "SPECCOST": {
                        "IOP-S": 0.26707598,
                        "DIESEL-L": 0.04285714,
                        "EL": 0.1,
                        "CO2-G": 0.04451862,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "N2-G": 0.01154,
                        "NG-G": 0.03056527,
                    },
                },
                "main_export_process_chain": [
                    {
                        "LIFETIME": 20,
                        "EFF": 0.98270994,
                        "FLH": 7000,
                        "OPEX-O": 0.00486257,
                        "CH4SHARE": {"NG-G": 0.909},
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "CBOUND": {"NG-G": 0.0548514},
                        "CONV": {"DIESEL-L": 0.00059456},
                        "LOSS": {"NG-G": 0.00378},
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    {
                        "LIFETIME": 20.0,
                        "EFF": 0.3360036,
                        "FLH": 7000,
                        "CAPEX": 0.59187636,
                        "OPEX-F": 0.01775629,
                        "CH4SHARE": {"NG-G": 0.909},
                        "EF_E": {"CH4-G": 201.0, "NG-G": 201.0},
                        "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                        "CBOUND": {"NG-G": 0.04081161},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"IOP-S": 1.37373737, "EL": 0.47685859},
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV",
                    },
                ],
                "main_transport_process_chain": [
                    {
                        "OPEX-T": 3.8e-07,
                        "EFF": 1.0,
                        "DIST": 12830.0,
                        "process_code": "DRI-SB#B",
                        "step": "SHP",
                    }
                ],
                "main_import_process_chain": [
                    {
                        "LIFETIME": 20.0,
                        "EFF": 1.01010101,
                        "FLH": 7000,
                        "CAPEX": 0.41734427,
                        "OPEX-F": 0.01252033,
                        "OPEX-O": 0.18367869,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    }
                ],
                "secondary_process": {
                    "EL": {
                        "LIFETIME": 30.0,
                        "EFF": 0.50491129,
                        "FLH": 7000,
                        "CAPEX": 2408.19070902,
                        "OPEX-F": 63.75889534,
                        "CH4SHARE": {"NG-G": 0.909},
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "process_code": "CCGT-CC#B",
                    },
                    "CO2-C": {
                        "LIFETIME": 20,
                        "EFF": 0.95,
                        "FLH": 7000,
                        "OPEX-O": 0.03024746,
                        "EF_E": {},
                        "EF_M": {},
                        "process_code": "CO2-T+S#B",
                    },
                },
            },
            # marks=pytest.mark.skip,  # noqa
        ),
        # =============================================================================
        # CASE 2
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Algeria",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_demand",  # sheet 41
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "context": {"source_region_code": "DZA", "target_country_code": "DEU"},
                "main_export_process_chain": [
                    {
                        "CBOUND": {"NG-G": 0.0548514},
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"DIESEL-L": 0.00060236},
                        "EFF": 0.90362604,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": {"NG-G": 0.0139},
                        "OPEX-O": 0.00316265,
                        "WACC": 0.14554836,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    {
                        "CAPEX": 408.10708157,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"EL": 0.00274153},
                        "EFF": 0.85708919,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "LOSS": {"NG-G": 0.0005},
                        "OPEX-F": 8.16214163,
                        "WACC": 0.14554836,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                ],
                "main_import_process_chain": [
                    {
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CONV": {"DIESEL-L": 2e-06, "EL": 0.00048, "NG-G": 0.00085},
                        "EFF": 1.0,
                        "EF_E": {
                            "DIESEL-L": 266.76,
                            "EL": 100.0,
                            "NG-G": 201.0,
                            "NG-L": 201.0,
                        },
                        "EF_M": {
                            "DIESEL-L": 266.76,
                            "EL": 100.0,
                            "NG-G": 201.0,
                            "NG-L": 201.0,
                        },
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": {"NG-G": 4e-08},
                        "WACC": 0.0423,
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                    {
                        "CAPEX": 0.59187636,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"EL": 0.47685859, "IOP-S": 1.37373737},
                        "EFF": 0.3360036,
                        "EF_E": {
                            "CH4-G": 201.0,
                            "CO2-C": 1.0,
                            "EL": 100.0,
                            "NG-G": 201.0,
                        },
                        "EF_M": {
                            "CH4-G": 201.0,
                            "CO2-C": 1.0,
                            "EL": 100.0,
                            "NG-G": 201.0,
                        },
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01775629,
                        "WACC": 0.0423,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    {
                        "CAPEX": 0.41734427,
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "EFF": 1.01010101,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01252033,
                        "OPEX-O": 0.18367869,
                        "WACC": 0.0423,
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                ],
                "main_transport_process_chain": [
                    {
                        "CONV": {"BFUEL-L": 0.01047548},
                        "CONV-OT": {"BFUEL-L": 3.3e-06},
                        "DIST": 3174.14,
                        "DST-S-D": 3174.14,
                        "DST-S-DP": 3000.0,
                        "EFF": 1.0,
                        "EF_E": {"NG-L": 201.0},
                        "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                        "SEASHARE": 0.1,
                        "process_code": "CH4-SB#B",
                        "step": "SHP",
                    }
                ],
                "parameter": {
                    "SPECCOST": {
                        "BFUEL-L": 0.00322434,
                        "CO2-G": 0.04451862,
                        "DIESEL-L": 0.04285714,
                        "EL": 0.08078,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "N2-G": 0.01154,
                    },
                    "WACC": 0.14554836,
                },
                "parameter_import": {
                    "SPECCOST": {
                        "BFUEL-L": 0.00322434,
                        "CO2-G": 0.04451862,
                        "DIESEL-L": 0.04285714,
                        "EL": 0.1,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "IOP-S": 0.26707598,
                        "N2-G": 0.01154,
                        "NG-G": 0.03056527,
                    },
                    "WACC": 0.0423,
                },
                "secondary_process": {
                    "CO2-C": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1.0},
                        "EF_M": {"CO2-C": 1.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.11656581,
                        "WACC": 0.14554836,
                        "process_code": "CO2-T+S#B",
                    },
                    "EL": {
                        "CAPEX": 2408.19070902,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.75889534,
                        "WACC": 0.14554836,
                        "process_code": "CCGT-CC#B",
                    },
                },
                "secondary_process_import": {
                    "CO2-C": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1.0, "EL": 100.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.14792048,
                        "WACC": 0.0423,
                        "process_code": "CO2-T+S#B",
                    }
                },
            },
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data_2(api_kwargs, expected):
    """Data test for blue iron chain using current data."""
    data_handler = DataHandler(
        scenario=api_kwargs["scenario"],
        data_dir=DEFAULT_DATA_DIR,
        user_data=None,
    )
    chain_def, tool_version_color, _optimize_flh = (
        _translate_and_validate_user_settings(**api_kwargs)
    )
    assert tool_version_color == "blue"

    chain_process = PtxCalc.get_or_create(chain_def)

    actual = chain_process.get_calculation_data(
        data_handler=data_handler,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
    )
    assert_deep_equal_approx(expected, actual, allow_new_dict_items=True)
