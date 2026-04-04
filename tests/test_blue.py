"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, PtxCalc, _translate_and_validate_user_settings
from ptxboa.api_data import DEFAULT_DATA_DIR, ChainProcess, DataHandler
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
    chain_proc = ChainProcess.get_or_create(chain_def)

    data = data_handler.get_calculation_data(
        chain_proc=chain_proc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=False,
    )
    ptxcalc_results = PtxCalc.calculate(chain_proc=chain_proc, data=data)

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

    # round and sort for easier comparison
    values = ptxcalc_results.results_flows_chain

    expected = {
        "calculation_data": {
            "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
            "parameter": {
                "SPECCOST": {
                    "EL": 0.08078,
                    "CO2-G": 0.04451862,
                    "H2O-L": 0.0013738,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                }
            },
            "parameter_import": {
                "SPECCOST": {
                    "EL": 0.08078,
                    "CO2-G": 0.04451862,
                    "H2O-L": 0.0013738,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                }
            },
            "main_export_process_chain": [
                {
                    "LIFETIME": 20,
                    "EFF": 1.0,
                    "FLH": 7000,
                    "CH4SHARE": {"NG-G": 0.909},
                    "EF_E": {"NG-G": 201.0},
                    "EF_M": {"NG-G": 201.0},
                    "process_code": "NG-PROD#B",
                    "step": "NG_PROD",
                },
                {
                    "LIFETIME": 20,
                    "EFF": 0.32000381,
                    "FLH": 7000,
                    "CAPEX": 0.591876,
                    "OPEX-F": 0.017756,
                    "CH4SHARE": {"NG-G": 0.909},
                    "EF_E": {"NG-G": 201.0, "EL": 402.0, "CH4-G": 201.0},
                    "EF_M": {"NG-G": 201.0, "CH4-G": 201.0},
                    "CBOUND": {"NG-G": 0.040812},
                    "CO2CPT-R": {"NG-G": 0.9, "CH4-G": 0.9},
                    "CO2CPT-S": {"NG-G": 0.45, "CH4-G": 0.45},
                    "CONV": {"CO2-C": 1, "EL": 0.476859, "IOP-S": 1.373737},
                    "LOSS": 0.05,
                    "process_code": "NG-DRI-C#B",
                    "step": "DERIV",
                },
            ],
            "main_transport_process_chain": [
                {"EFF": 1.0, "DIST": 999.0, "process_code": "DRI-SB#B", "step": "SHP"}
            ],
            "main_import_process_chain": [
                {
                    "LIFETIME": 20,
                    "EFF": 1.010101,
                    "FLH": 7000,
                    "CAPEX": 0.417344,
                    "OPEX-F": 0.01252,
                    "OPEX-O": 0.183679,
                    "CH4SHARE": {"NG-G": 0.909},
                    "EF_E": {"EL": 300.0},
                    "EF_M": {"NG-G": 201.0},
                    "CBOUND": {"STL-S": 0.00396},
                    "CONV": {"NG-G": 0.0042, "EL": 0.651},
                    "LOSS_FLOW": {"NG-G": 0.05},
                    "process_code": "EAF#B",
                    "step": "DERIV_I",
                }
            ],
            "secondary_process": {
                "EL": {
                    "LIFETIME": 20,
                    "EFF": 1.0,
                    "FLH": 7000,
                    "CH4SHARE": {"NG-G": 0.909},
                    "EF_E": {"NG-G": 201.0, "EL": 402.0},
                    "EF_M": {"NG-G": 201.0},
                    "process_code": "CCGT-CC#B",
                },
                "CO2-C": {
                    "LIFETIME": 20,
                    "EFF": 1.0,
                    "FLH": 7000,
                    "EF_E": {"EL": 402.0},
                    "process_code": "CO2-T+S#B",
                },
            },
        },
        "flow_values": [
            {
                "process_code": "NG-DRI-C#B",
                "process_step": "DERIV",
                "main_input": 3.0937132,
                "main_output": 0.99000001,
                "flows": {"CO2-C": 1.22985117, "EL": 0.47209041, "IOP-S": 1.35999964},
                "emissions": {
                    "co2_in_flows_e": 592.22509848,
                    "co2_captured_e": 239.85116488,
                    "co2_bound_in_product_e": 148.05784985,
                    "co2_direct_e": 204.31608375,
                    "co2_indirect_scope2_e": 189.78034672,
                    "ch4_direct_e": 9.20718815,
                    "ch4_direct_co2e_e": 274.37420694,
                    "co2e_total_direct_e": 478.69029069,
                    "co2_in_flows_m": 592.22509848,
                    "co2_captured_m": 239.85116488,
                    "co2_bound_in_product_m": 148.05784985,
                    "co2_direct_m": 204.31608375,
                    "co2_indirect_scope2_m": 189.78034672,
                    "ch4_direct_m": 9.20718815,
                    "ch4_direct_co2e_m": 274.37420694,
                    "co2e_total_direct_m": 478.69029069,
                },
            },
            {
                "process_code": "EAF#B",
                "process_step": "DERIV_I",
                "main_input": 0.99000001,
                "main_output": 1.0,
                "flows": {"NG-G": 0.0042, "EL": 0.651},
                "emissions": {
                    "co2_bound_in_product_last_proc_e": 148.05784985,
                    "co2_direct_e": 148.05784985,
                    "co2_indirect_scope2_e": 195.3,
                    "ch4_direct_e": 0.0124996,
                    "ch4_direct_co2e_e": 0.3724882,
                    "co2e_total_direct_e": 148.43033805,
                    "co2_bound_in_product_last_proc_m": 148.05784985,
                    "co2_in_flows_m": 0.804,
                    "co2_direct_m": 148.86184985,
                    "co2_indirect_scope2_m": 195.3,
                    "ch4_direct_m": 0.0124996,
                    "ch4_direct_co2e_m": 0.3724882,
                    "co2e_total_direct_m": 149.23433805,
                },
            },
            {
                "process_code": "NG-PROD#B",
                "process_step": "NG_PROD",
                "main_input": 3.0937132,
                "main_output": 3.0937132,
                "emissions": {
                    "co2_in_flows_e": 621.8363534,
                    "co2_direct_e": 621.8363534,
                    "co2e_total_direct_e": 621.8363534,
                    "co2_in_flows_m": 621.8363534,
                    "co2_direct_m": 621.8363534,
                    "co2e_total_direct_m": 621.8363534,
                },
            },
            {
                "process_code": "DRI-SB#B",
                "process_step": "SHP",
                "main_input": 0.99000001,
                "main_output": 0.99000001,
                "emissions": {
                    "co2_bound_in_product_last_proc_e": 148.05784985,
                    "co2_bound_in_product_e": 148.05784985,
                    "co2_bound_in_product_last_proc_m": 148.05784985,
                    "co2_bound_in_product_m": 148.05784985,
                },
            },
        ],
        "res_emission_mass": [
            {
                "process_subtype": "EAF#B",
                "emission_type": "direct",
                "gas_type": "CH4",
                "values": 372.48820245,
            },
            {
                "process_subtype": "EAF#B",
                "emission_type": "direct",
                "gas_type": "CO2",
                "values": 148861.8498502,
            },
            {
                "process_subtype": "EAF#B",
                "emission_type": "indirect",
                "gas_type": "CO2",
                "values": 195300.0,
            },
            {
                "process_subtype": "NG-DRI-C#B",
                "emission_type": "direct",
                "gas_type": "CH4",
                "values": 274374.2069403,
            },
            {
                "process_subtype": "NG-DRI-C#B",
                "emission_type": "direct",
                "gas_type": "CO2",
                "values": 204316.0837458,
            },
            {
                "process_subtype": "NG-DRI-C#B",
                "emission_type": "indirect",
                "gas_type": "CO2",
                "values": 189780.3467178,
            },
            {
                "process_subtype": "CCGT-CC#B",
                "emission_type": "direct",
                "gas_type": "CO2",
                "values": 94890.1733589,
            },
            {
                "process_subtype": "NG-PROD#B",
                "emission_type": "direct",
                "gas_type": "CO2",
                "values": 621836.35340471,
            },
        ],
    }
    actually = {
        "calculation_data": data,
        "flow_values": sorted(values, key=lambda x: x["process_step"]),  # type: ignore
        "res_emission_mass": res_emission_mass,
    }

    assert_deep_equal_approx(expected, actually)


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
                            "LOSS": 0.00378,
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
                            "EF_E": {"CO2-C": 1.0, "CH4-G": 201.0, "NG-G": 201.0},
                            "EF_M": {"CO2-C": 1.0, "CH4-G": 201.0, "NG-G": 201.0},
                            "CBOUND": {"NG-G": 0.04081161},
                            "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                            "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                            "CONV": {"CO2-C": 1, "IOP-S": 1.37373737, "EL": 0.47685859},
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
                            "EF_E": {"NG-G": 201.0, "CO2-C": 1.0},
                            "EF_M": {"NG-G": 201.0, "CO2-C": 1.0},
                            "CO2CPT-R": {"NG-G": 0.89777778},
                            "CO2CPT-S": {"NG-G": 1.0},
                            "process_code": "CCGT-CC#B",
                        },
                        "CO2-C": {
                            "LIFETIME": 20,
                            "EFF": 0.95,
                            "FLH": 7000,
                            "OPEX-O": 0.03024746,
                            "EF_E": {"CO2-C": 1.0},
                            "EF_M": {"CO2-C": 1.0},
                            "process_code": "CO2-T+S#B",
                        },
                    },
                },
                "flow_values": [
                    {
                        "process_code": "NG-DRI-C#B",
                        "process_step": "DERIV",
                        "main_input": 2.946397,
                        "main_output": 0.99,
                        "flows": {"IOP-S": 1.36, "CO2-C": 1.22985145, "EL": 0.47209},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 592.22579704,
                            "co2_in_flows_e": 593.215797,
                            "co2_captured_e": 239.85144778,
                            "co2_bound_in_product_e": 148.05644926,
                            "co2_direct_e": 797.53369699,
                            "co2e_total_direct_e": 797.53369699,
                            "co2_bound_in_product_last_proc_m": 592.22579704,
                            "co2_in_flows_m": 593.215797,
                            "co2_captured_m": 239.85144778,
                            "co2_bound_in_product_m": 148.05644926,
                            "co2_direct_m": 797.53369699,
                            "co2e_total_direct_m": 797.53369699,
                        },
                    },
                    {
                        "process_code": "EAF#B",
                        "process_step": "DERIV_I2",
                        "main_input": 0.99,
                        "main_output": 1.0,
                        "flows": {"EL": 0.651, "NG-G": 0.3},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 148.05644926,
                            "co2_in_flows_e": 60.3,
                            "co2_bound_in_product_e": 14.65778518,
                            "co2_direct_e": 193.69866408,
                            "co2_indirect_scope2_e": 65.1,
                            "co2e_total_direct_e": 193.69866408,
                            "co2_bound_in_product_last_proc_m": 148.05644926,
                            "co2_in_flows_m": 60.3,
                            "co2_bound_in_product_m": 14.65778518,
                            "co2_direct_m": 193.69866408,
                            "co2_indirect_scope2_m": 65.1,
                            "co2e_total_direct_m": 193.69866408,
                        },
                    },
                    {
                        "process_code": "NG-PROD#B",
                        "process_step": "NG_PROD",
                        "main_input": 2.99823669,
                        "main_output": 2.946397,
                        "flows": {"DIESEL-L": 0.0017518},
                        "emissions": {
                            "co2_in_flows_e": 600.84346303,
                            "co2_bound_in_product_e": 592.22579704,
                            "co2_direct_e": 8.61766599,
                            "ch4_direct_e": 0.70564365,
                            "ch4_direct_co2e_e": 21.02818078,
                            "co2e_total_direct_e": 29.64584677,
                            "co2_in_flows_m": 600.84346303,
                            "co2_bound_in_product_m": 592.22579704,
                            "co2_direct_m": 8.61766599,
                            "ch4_direct_m": 0.70564365,
                            "ch4_direct_co2e_m": 21.02818078,
                            "co2e_total_direct_m": 29.64584677,
                        },
                    },
                    {
                        "process_code": "CO2-T+S#B",
                        "process_step": "SECONDARY:CO2 transport and storage",
                        "main_input": 1.22985145,
                        "main_output": 1.22985145,
                        "emissions": {
                            "co2_in_flows_e": 1.22985145,
                            "co2_direct_e": 1.22985145,
                            "co2e_total_direct_e": 1.22985145,
                            "co2_in_flows_m": 1.22985145,
                            "co2_direct_m": 1.22985145,
                            "co2e_total_direct_m": 1.22985145,
                        },
                    },
                    {
                        "process_code": "CCGT-CC#B",
                        "process_step": "SECONDARY:Electricity generation",
                        "main_input": 0.47209,
                        "main_output": 0.47209,
                        "emissions": {
                            "co2_in_flows_e": 94.89009,
                            "co2_captured_e": 85.19021413,
                            "co2_direct_e": 9.69987587,
                            "co2e_total_direct_e": 9.69987587,
                            "co2_in_flows_m": 94.89009,
                            "co2_captured_m": 85.19021413,
                            "co2_direct_m": 9.69987587,
                            "co2e_total_direct_m": 9.69987587,
                        },
                    },
                    {
                        "process_code": "DRI-SB#B",
                        "process_step": "SHP",
                        "main_input": 0.99,
                        "main_output": 0.99,
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 148.05644926,
                            "co2_bound_in_product_e": 148.05644926,
                            "co2_bound_in_product_last_proc_m": 148.05644926,
                            "co2_bound_in_product_m": 148.05644926,
                        },
                    },
                ],
                "res_emission_mass": [
                    {
                        "process_subtype": "Bound in product",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 14657.78518,
                    },
                    {
                        "process_subtype": "CO2-T+S#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 1229.85144778,
                    },
                    {
                        "process_subtype": "EAF#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 193698.66407992,
                    },
                    {
                        "process_subtype": "EAF#B",
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "values": 65100.0,
                    },
                    {
                        "process_subtype": "NG-DRI-C#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 797533.69699477,
                    },
                    {
                        "process_subtype": "CCGT-CC#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 9699.87586667,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "values": 21028.18077976,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 8617.66599493,
                    },
                ],
                "res_costs": [
                    {
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.01470907,
                    },
                    {
                        "process_subtype": "CO2-T+S#B",
                        "process_type": "CO2 transport and storage",
                        "values": 0.03719989,
                    },
                    {
                        "process_subtype": "DRI-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00478268,
                    },
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
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.01440213,
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
                    "parameter": {
                        "WACC": 0.14554836,
                        "SPECCOST": {
                            "DIESEL-L": 0.04285714,
                            "EL": 0.08078,
                            "BFUEL-L": 0.00322434,
                            "CO2-G": 0.04451862,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "N2-G": 0.01154,
                        },
                    },
                    "parameter_import": {
                        "WACC": 0.0423,
                        "SPECCOST": {
                            "DIESEL-L": 0.04285714,
                            "EL": 0.1,
                            "NG-G": 0.03056527,
                            "BFUEL-L": 0.00322434,
                            "CO2-G": 0.04451862,
                            "H2O-L": 0.0013738,
                            "HEAT": 0.0577,
                            "N2-G": 0.01154,
                            "IOP-S": 0.26707598,
                        },
                    },
                    "main_export_process_chain": [
                        {
                            "LIFETIME": 20,
                            "EFF": 0.90362604,
                            "FLH": 7000,
                            "OPEX-O": 0.00316265,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                            "CBOUND": {"NG-G": 0.0548514},
                            "CONV": {"DIESEL-L": 0.00060236},
                            "LOSS": 0.0139,
                            "process_code": "NG-PROD#B",
                            "step": "NG_PROD",
                        }
                    ],
                    "main_transport_process_chain": [
                        {
                            "LIFETIME": 30.0,
                            "EFF": 0.85708919,
                            "FLH": 7000,
                            "CAPEX": 408.10708157,
                            "OPEX-F": 8.16214163,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "EF_E": {"NG-L": 201.0, "NG-G": 201.0},
                            "EF_M": {"NG-L": 201.0, "NG-G": 201.0},
                            "CONV": {"EL": 0.00274153},
                            "LOSS": 0.0005,
                            "process_code": "CH4-LIQ#B",
                            "step": "PRE_SHP",
                        },
                        {
                            "EF_E": {"NG-L": 201.0},
                            "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                            "CONV-OT": {"BFUEL-L": 3.3e-06, "NG-L": 1.15e-06},
                            "EFF": 1.0,
                            "DIST": 3174.14,
                            "process_code": "CH4-SB#B",
                            "step": "SHP",
                        },
                        {
                            "LIFETIME": 20,
                            "EFF": 1.0,
                            "FLH": 7000,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "EF_E": {"DIESEL-L": 266.76, "NG-L": 201.0, "NG-G": 201.0},
                            "EF_M": {"DIESEL-L": 266.76, "NG-L": 201.0, "NG-G": 201.0},
                            "CONV": {"DIESEL-L": 2e-06, "EL": 0.00048, "NG-G": 0.00085},
                            "LOSS_FLOW": {"NG-G": 4e-08},
                            "process_code": "CH4-RGAS#B",
                            "step": "POST_SHP",
                        },
                    ],
                    "main_import_process_chain": [
                        {
                            "LIFETIME": 20.0,
                            "EFF": 0.3360036,
                            "FLH": 7000,
                            "CAPEX": 0.59187636,
                            "OPEX-F": 0.01775629,
                            "CH4SHARE": {"NG-G": 0.92080641},
                            "EF_E": {
                                "CH4-G": 201.0,
                                "CO2-C": 1.0,
                                "NG-G": 201.0,
                                "EL": 100.0,
                            },
                            "EF_M": {
                                "CH4-G": 201.0,
                                "CO2-C": 1.0,
                                "NG-G": 201.0,
                                "EL": 100.0,
                            },
                            "CBOUND": {"NG-G": 0.04081161},
                            "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                            "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                            "CONV": {"CO2-C": 1, "EL": 0.47685859, "IOP-S": 1.37373737},
                            "process_code": "NG-DRI-C#B",
                            "step": "DERIV_I",
                        },
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
                        },
                    ],
                    "secondary_process": {
                        "EL": {
                            "LIFETIME": 30.0,
                            "EFF": 0.50491129,
                            "FLH": 7000,
                            "CAPEX": 2408.19070902,
                            "OPEX-F": 63.75889534,
                            "CH4SHARE": {"NG-G": 0.89953333},
                            "EF_E": {"NG-G": 201.0, "CO2-C": 1.0},
                            "EF_M": {"NG-G": 201.0, "CO2-C": 1.0},
                            "CO2CPT-R": {"NG-G": 0.89777778},
                            "CO2CPT-S": {"NG-G": 1.0},
                            "process_code": "CCGT-CC#B",
                        },
                        "CO2-C": {
                            "LIFETIME": 20,
                            "EFF": 0.95,
                            "FLH": 7000,
                            "OPEX-O": 0.11656581,
                            "EF_E": {"CO2-C": 1.0},
                            "EF_M": {"CO2-C": 1.0},
                            "process_code": "CO2-T+S#B",
                        },
                    },
                    "secondary_process_import": {
                        "CO2-C": {
                            "LIFETIME": 20,
                            "EFF": 0.95,
                            "FLH": 7000,
                            "OPEX-O": 0.14792048,
                            "EF_E": {"EL": 100.0, "CO2-C": 1.0},
                            "EF_M": {"EL": 100.0, "CO2-C": 1.0},
                            "process_code": "CO2-T+S#B",
                        }
                    },
                },
                "flow_values": [
                    {
                        "process_code": "NG-DRI-C#B",
                        "process_step": "DERIV_I",
                        "main_input": 2.946397,
                        "main_output": 0.99,
                        "flows": {"EL": 0.47209, "CO2-C": 1.22985145, "IOP-S": 1.36},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 592.22579704,
                            "co2_in_flows_e": 593.215797,
                            "co2_captured_e": 239.85144778,
                            "co2_bound_in_product_e": 148.05644926,
                            "co2_direct_e": 797.53369699,
                            "co2_indirect_scope2_e": 47.209,
                            "co2e_total_direct_e": 797.53369699,
                            "co2_bound_in_product_last_proc_m": 592.22579704,
                            "co2_in_flows_m": 593.215797,
                            "co2_captured_m": 239.85144778,
                            "co2_bound_in_product_m": 148.05644926,
                            "co2_direct_m": 797.53369699,
                            "co2_indirect_scope2_m": 47.209,
                            "co2e_total_direct_m": 797.53369699,
                        },
                    },
                    {
                        "process_code": "EAF#B",
                        "process_step": "DERIV_I2",
                        "main_input": 0.99,
                        "main_output": 1.0,
                        "flows": {"NG-G": 0.3, "EL": 0.651},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 148.05644926,
                            "co2_in_flows_e": 60.3,
                            "co2_bound_in_product_e": 14.65778518,
                            "co2_direct_e": 193.69866408,
                            "co2_indirect_scope2_e": 65.1,
                            "co2e_total_direct_e": 193.69866408,
                            "co2_bound_in_product_last_proc_m": 148.05644926,
                            "co2_in_flows_m": 60.3,
                            "co2_bound_in_product_m": 14.65778518,
                            "co2_direct_m": 193.69866408,
                            "co2_indirect_scope2_m": 65.1,
                            "co2e_total_direct_m": 193.69866408,
                        },
                    },
                    {
                        "process_code": "NG-PROD#B",
                        "process_step": "NG_PROD",
                        "main_input": 3.80431534,
                        "main_output": 3.43767842,
                        "flows": {"DIESEL-L": 0.00207073},
                        "emissions": {
                            "co2_in_flows_e": 754.73661186,
                            "co2_bound_in_product_e": 690.97336284,
                            "co2_direct_e": 63.76324902,
                            "ch4_direct_e": 3.22563948,
                            "ch4_direct_co2e_e": 96.12405658,
                            "co2e_total_direct_e": 159.8873056,
                            "co2_in_flows_m": 754.73661186,
                            "co2_bound_in_product_m": 690.97336284,
                            "co2_direct_m": 63.76324902,
                            "ch4_direct_m": 3.22563948,
                            "ch4_direct_co2e_m": 96.12405658,
                            "co2e_total_direct_m": 159.8873056,
                        },
                    },
                    {
                        "process_code": "CH4-RGAS#B",
                        "process_step": "POST_SHP",
                        "main_input": 2.946397,
                        "main_output": 2.946397,
                        "flows": {
                            "NG-G": 0.00250444,
                            "EL": 0.00141427,
                            "DIESEL-L": 5.89e-06,
                        },
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 592.22579704,
                            "co2_in_flows_e": 592.73076089,
                            "co2_bound_in_product_e": 592.22579704,
                            "co2_direct_e": 592.73076089,
                            "ch4_direct_e": 1e-08,
                            "ch4_direct_co2e_e": 1.8e-07,
                            "co2e_total_direct_e": 592.73076107,
                            "co2_bound_in_product_last_proc_m": 592.22579704,
                            "co2_in_flows_m": 592.73076089,
                            "co2_bound_in_product_m": 592.22579704,
                            "co2_direct_m": 592.73076089,
                            "ch4_direct_m": 1e-08,
                            "ch4_direct_co2e_m": 1.8e-07,
                            "co2e_total_direct_m": 592.73076107,
                        },
                    },
                    {
                        "process_code": "CH4-LIQ#B",
                        "process_step": "PRE_SHP",
                        "main_input": 3.43767842,
                        "main_output": 2.946397,
                        "flows": {"EL": 0.00807763},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 690.97336284,
                            "co2_in_flows_e": 690.62804877,
                            "co2_bound_in_product_e": 592.22579704,
                            "co2_direct_e": 789.37561457,
                            "ch4_direct_e": 0.10625217,
                            "ch4_direct_co2e_e": 3.1663146,
                            "co2e_total_direct_e": 792.54192918,
                            "co2_bound_in_product_last_proc_m": 690.97336284,
                            "co2_in_flows_m": 690.62804877,
                            "co2_bound_in_product_m": 592.22579704,
                            "co2_direct_m": 789.37561457,
                            "ch4_direct_m": 0.10625217,
                            "ch4_direct_co2e_m": 3.1663146,
                            "co2e_total_direct_m": 792.54192918,
                        },
                    },
                    {
                        "process_code": "CCGT-CC#B",
                        "process_step": "SECONDARY:Electricity generation",
                        "main_input": 0.0094919,
                        "main_output": 0.0094919,
                        "emissions": {
                            "co2_direct_e": 0.19502696,
                            "co2_direct_m": 0.19502696,
                            "co2_captured_e": 1.71284548,
                            "co2e_total_direct_e": 0.19502696,
                            "co2_captured_m": 1.71284548,
                            "co2_in_flows_m": 1.90787244,
                            "co2e_total_direct_m": 0.19502696,
                            "co2_in_flows_e": 1.90787244,
                        },
                    },
                    {
                        "process_code": "CH4-SB#B",
                        "process_step": "SHP",
                        "main_input": 2.946397,
                        "main_output": 2.946397,
                        "flows": {"NG-L": 0.01079023, "BFUEL-L": 0.03086494},
                        "emissions": {
                            "co2_bound_in_product_last_proc_e": 592.22579704,
                            "co2_in_flows_e": 594.39463225,
                            "co2_bound_in_product_e": 592.22579704,
                            "co2_direct_e": 594.39463225,
                            "co2e_total_direct_e": 594.39463225,
                            "co2_bound_in_product_last_proc_m": 592.22579704,
                            "co2_in_flows_m": 603.42818167,
                            "co2_bound_in_product_m": 592.22579704,
                            "co2_direct_m": 603.42818167,
                            "co2e_total_direct_m": 603.42818167,
                        },
                    },
                ],
                "res_emission_mass": [
                    {
                        "process_subtype": "Bound in product",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 14657.78518,
                    },
                    {
                        "process_subtype": "EAF#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 193698.66407992,
                    },
                    {
                        "process_subtype": "EAF#B",
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "values": 65100.0,
                    },
                    {
                        "process_subtype": "NG-DRI-C#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 797533.69699477,
                    },
                    {
                        "process_subtype": "NG-DRI-C#B",
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "values": 47209.0,
                    },
                    {
                        "process_subtype": "CCGT-CC#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 195.02696044,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "values": 96124.05658408,
                    },
                    {
                        "process_subtype": "NG-PROD#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 63763.24901687,
                    },
                    {
                        "process_subtype": "CH4-LIQ#B",
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "values": 3166.31460453,
                    },
                    {
                        "process_subtype": "CH4-LIQ#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 789375.61457463,
                    },
                    {
                        "process_subtype": "CH4-RGAS#B",
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "values": 0.00018463,
                    },
                    {
                        "process_subtype": "CH4-RGAS#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 592730.76088918,
                    },
                    {
                        "process_subtype": "CH4-SB#B",
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "values": 603428.18167276,
                    },
                ],
                "res_costs": [
                    {
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.00056994,
                    },
                    {
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.02886908,
                    },
                    {
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 2.5e-07,
                    },
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
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.0109609,
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
    values = sorted(values, key=lambda x: x["process_step"])  # type: ignore

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
    assert_deep_equal_approx(expected, actual)


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
                        "LOSS": 0.00378,
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
                        "EF_E": {"CO2-C": 1.0, "CH4-G": 201.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1.0, "CH4-G": 201.0, "NG-G": 201.0},
                        "CBOUND": {"NG-G": 0.04081161},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "IOP-S": 1.37373737, "EL": 0.47685859},
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
                        "EF_E": {"CO2-C": 1.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1.0, "NG-G": 201.0},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "process_code": "CCGT-CC#B",
                    },
                    "CO2-C": {
                        "LIFETIME": 20,
                        "EFF": 0.95,
                        "FLH": 7000,
                        "OPEX-O": 0.03024746,
                        "EF_E": {"CO2-C": 1.0},
                        "EF_M": {"CO2-C": 1.0},
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
                "parameter": {
                    "WACC": 0.14554836,
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.08078,
                        "BFUEL-L": 0.00322434,
                        "CO2-G": 0.04451862,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "N2-G": 0.01154,
                    },
                },
                "parameter_import": {
                    "WACC": 0.0423,
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.1,
                        "NG-G": 0.03056527,
                        "BFUEL-L": 0.00322434,
                        "CO2-G": 0.04451862,
                        "H2O-L": 0.0013738,
                        "HEAT": 0.0577,
                        "N2-G": 0.01154,
                        "IOP-S": 0.26707598,
                    },
                },
                "main_export_process_chain": [
                    {
                        "LIFETIME": 20,
                        "EFF": 0.90362604,
                        "FLH": 7000,
                        "OPEX-O": 0.00316265,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "EF_E": {"NG-G": 201.0, "DIESEL-L": 266.76},
                        "EF_M": {"NG-G": 201.0, "DIESEL-L": 266.76},
                        "CBOUND": {"NG-G": 0.0548514},
                        "CONV": {"DIESEL-L": 0.00060236},
                        "LOSS": 0.0139,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    }
                ],
                "main_transport_process_chain": [
                    {
                        "LIFETIME": 30.0,
                        "EFF": 0.85708919,
                        "FLH": 7000,
                        "CAPEX": 408.10708157,
                        "OPEX-F": 8.16214163,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "EF_E": {"NG-G": 201.0, "NG-L": 201.0},
                        "EF_M": {"NG-G": 201.0, "NG-L": 201.0},
                        "CONV": {"EL": 0.00274153},
                        "LOSS": 0.0005,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                    {
                        "EF_E": {"NG-L": 201.0},
                        "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                        "CONV-OT": {"BFUEL-L": 3.3e-06, "NG-L": 1.15e-06},
                        "EFF": 1.0,
                        "DIST": 3174.14,
                        "process_code": "CH4-SB#B",
                        "step": "SHP",
                    },
                    {
                        "LIFETIME": 20,
                        "EFF": 1.0,
                        "FLH": 7000,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "EF_E": {"NG-G": 201.0, "DIESEL-L": 266.76, "NG-L": 201.0},
                        "EF_M": {"NG-G": 201.0, "DIESEL-L": 266.76, "NG-L": 201.0},
                        "CONV": {"NG-G": 0.00085, "EL": 0.00048, "DIESEL-L": 2e-06},
                        "LOSS_FLOW": {"NG-G": 4e-08},
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                ],
                "main_import_process_chain": [
                    {
                        "LIFETIME": 20.0,
                        "EFF": 0.3360036,
                        "FLH": 7000,
                        "CAPEX": 0.59187636,
                        "OPEX-F": 0.01775629,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "EF_E": {
                            "CH4-G": 201.0,
                            "NG-G": 201.0,
                            "CO2-C": 1.0,
                            "EL": 100.0,
                        },
                        "EF_M": {
                            "CH4-G": 201.0,
                            "NG-G": 201.0,
                            "CO2-C": 1.0,
                            "EL": 100.0,
                        },
                        "CBOUND": {"NG-G": 0.04081161},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"IOP-S": 1.37373737, "CO2-C": 1, "EL": 0.47685859},
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    {
                        "LIFETIME": 20.0,
                        "EFF": 1.01010101,
                        "FLH": 7000,
                        "CAPEX": 0.41734427,
                        "OPEX-F": 0.01252033,
                        "OPEX-O": 0.18367869,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "EF_E": {"NG-G": 201.0, "EL": 100.0},
                        "EF_M": {"NG-G": 201.0, "EL": 100.0},
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CONV": {"NG-G": 0.3, "EL": 0.651},
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                ],
                "secondary_process": {
                    "EL": {
                        "LIFETIME": 30.0,
                        "EFF": 0.50491129,
                        "FLH": 7000,
                        "CAPEX": 2408.19070902,
                        "OPEX-F": 63.75889534,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "EF_E": {"NG-G": 201.0, "CO2-C": 1.0},
                        "EF_M": {"NG-G": 201.0, "CO2-C": 1.0},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "process_code": "CCGT-CC#B",
                    },
                    "CO2-C": {
                        "LIFETIME": 20,
                        "EFF": 0.95,
                        "FLH": 7000,
                        "OPEX-O": 0.11656581,
                        "EF_E": {"CO2-C": 1.0},
                        "EF_M": {"CO2-C": 1.0},
                        "process_code": "CO2-T+S#B",
                    },
                },
                "secondary_process_import": {
                    "CO2-C": {
                        "LIFETIME": 20,
                        "EFF": 0.95,
                        "FLH": 7000,
                        "OPEX-O": 0.14792048,
                        "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1.0, "EL": 100.0},
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

    chain_process = ChainProcess.get_or_create(chain_def)

    actual = chain_process.get_calculation_data(
        data_handler=data_handler,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
    )
    assert_deep_equal_approx(expected, actual)
