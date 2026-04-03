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


# recursively use pytest.approx
@pytest.mark.parametrize(
    "scenario, kwargs, api_kwargs",
    [
        [
            "2040 (medium)",
            {
                "chain_name": "Blue Iron (blue)*",
                "source_region_code": "QAT",
                "target_country_code": "DEU",
                "process_code_res": None,
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
    calculation_data = data_handler.get_calculation_data(
        ChainDef(**kwargs), optimize_flh=False
    )
    ptxcalc_results = PtxCalc.calculate(calculation_data)  # type: ignore

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

    calculation_data_exp = {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "main_export_process_chain": [
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
            {
                "CAPEX": 0.591876,
                "CBOUND": {"NG-G": 0.040812},
                "CH4SHARE": {"NG-G": 0.909},
                "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                "CONV": {"CO2-C": 1, "EL": 0.476859, "IOP-S": 1.373737},
                "EFF": 0.320004,
                "EF_E": {"CH4-G": 201.0, "EL": 402.0, "NG-G": 201.0},
                "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS": 0.05,
                "OPEX-F": 0.017756,
                "process_code": "NG-DRI-C#B",
                "step": "DERIV",
            },
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0.417344,
                "CBOUND": {"STL-S": 0.00396},
                "CH4SHARE": {"NG-G": 0.909},
                "CONV": {"EL": 0.651, "NG-G": 0.0042},
                "EFF": 1.010101,
                "EF_E": {"EL": 300.0},
                "EF_M": {"NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS_FLOW": {"NG-G": 0.05},
                "OPEX-F": 0.01252,
                "OPEX-O": 0.183679,
                "process_code": "EAF#B",
                "step": "DERIV_I",
            }
        ],
        "parameter": {"SPECCOST": {"EL": 0.08078}},
        "parameter_i": {"SPECCOST": {"EL": 0.08078}},
        "secondary_process": {
            "CO2-C": {
                "EFF": 1.0,
                "EF_E": {"EL": 402.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "process_code": "CO2-T+S#B",
            },
            "EL": {
                "CH4SHARE": {"NG-G": 0.909},
                "EFF": 1.0,
                "EF_E": {"EL": 402.0, "NG-G": 201.0},
                "EF_M": {"NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "process_code": "CCGT-CC#B",
            },
        },
        "transport_process_chain": [
            {"DIST": 999.0, "EFF": 1, "process_code": "DRI-SB#B", "step": "SHP"}
        ],
    }
    values_exp = [
        {
            "emissions": {
                "co2_direct_e": 621.836353,
                "co2_direct_m": 621.836353,
                "co2_in_flows_e": 621.836353,
                "co2_in_flows_m": 621.836353,
                "co2e_total_direct_e": 621.836353,
                "co2e_total_direct_m": 621.836353,
            },
            "main_input": 3.093713,
            "main_output": 3.093713,
            "process_code": "NG-PROD#B",
            "process_step": "NG_PROD",
        },
        {
            "emissions": {
                "ch4_direct_co2e_e": 274.374207,
                "ch4_direct_co2e_m": 274.374207,
                "ch4_direct_e": 9.207188,
                "ch4_direct_m": 9.207188,
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_m": 148.05785,
                "co2_captured_e": 239.851165,
                "co2_captured_m": 239.851165,
                "co2_direct_e": 204.316084,
                "co2_direct_m": 204.316084,
                "co2_in_flows_e": 592.225098,
                "co2_in_flows_m": 592.225098,
                "co2e_total_direct_e": 478.690291,
                "co2e_total_direct_m": 478.690291,
            },
            "flows": {"CO2-C": 0.239851},
            "main_input": 3.093713,
            "main_output": 0.99,
            "process_code": "NG-DRI-C#B",
            "process_step": "DERIV",
        },
        {
            "emissions": {
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_bound_in_product_m": 148.05785,
            },
            "main_input": 0.99,
            "main_output": 0.99,
            "process_code": "DRI-SB#B",
            "process_step": "SHP",
        },
        {
            "emissions": {
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_direct_e": 148.05785,
                "co2_direct_m": 148.05785,
                "co2e_total_direct_e": 148.05785,
                "co2e_total_direct_m": 148.05785,
            },
            "main_input": 0.99,
            "main_output": 1.0,
            "process_code": "EAF#B",
            "process_step": "DERIV_I",
        },
    ]
    res_emission_mass_exp = [
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "EAF#B",
            "values": 148057.84985,
        },
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "NG-DRI-C#B",
            "values": 274374.20694,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "NG-DRI-C#B",
            "values": 204316.083746,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "NG-PROD#B",
            "values": 621836.353405,
        },
    ]

    assert_deep_equal_approx(calculation_data_exp, calculation_data)
    assert_deep_equal_approx(calculation_data_exp, calculation_data)
    assert_deep_equal_approx(values_exp, values)
    assert_deep_equal_approx(res_emission_mass_exp, res_emission_mass)


@pytest.mark.parametrize(
    "api_kwargs,calculation_data_exp,values_exp,res_emission_mass_exp,res_costs_exp",
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
                "main_export_process_chain": [
                    {
                        "CBOUND": {"NG-G": 0.0548514},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV": {"DIESEL-L": 0.00059456},
                        "EFF": 0.98270994,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": 0.00378,
                        "OPEX-O": 0.00486257,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    {
                        "CAPEX": 0.59187636,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "EL": 0.47685859, "IOP-S": 1.37373737},
                        "EFF": 0.3360036,
                        "EF_E": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                        "EF_M": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01775629,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV",
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
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    }
                ],
                "parameter": {
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.08078,
                        "IOP-S": 0.26707598,
                    },
                    "WACC": 0.0487,
                },
                "parameter_i": {
                    "SPECCOST": {"EL": 0.1, "NG-G": 0.03056527},
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
                        "process_code": "CCGT-CC#B",
                    },
                },
                "transport_process_chain": [
                    {
                        "DIST": 12830.0,
                        "EFF": 1,
                        "OPEX-T": 3.8e-07,
                        "process_code": "DRI-SB#B",
                        "step": "SHP",
                    }
                ],
            },
            [
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 21.02818078,
                        "ch4_direct_co2e_m": 21.02818078,
                        "ch4_direct_e": 0.70564365,
                        "ch4_direct_m": 0.70564365,
                        "co2_bound_in_product_e": 592.22579704,
                        "co2_bound_in_product_m": 592.22579704,
                        "co2_direct_e": 8.15035506,
                        "co2_direct_m": 8.15035506,
                        "co2_in_flows_e": 600.3761521,
                        "co2_in_flows_m": 600.3761521,
                        "co2e_total_direct_e": 29.17853584,
                        "co2e_total_direct_m": 29.17853584,
                    },
                    "main_input": 2.99823669,
                    "main_output": 2.946397,
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.05644926,
                        "co2_bound_in_product_last_proc_e": 592.22579704,
                        "co2_bound_in_product_last_proc_m": 592.22579704,
                        "co2_bound_in_product_m": 148.05644926,
                        "co2_captured_e": 239.85144778,
                        "co2_captured_m": 239.85144778,
                        "co2_direct_e": 796.54369699,
                        "co2_direct_m": 796.54369699,
                        "co2_in_flows_e": 592.225797,
                        "co2_in_flows_m": 592.225797,
                        "co2e_total_direct_e": 796.54369699,
                        "co2e_total_direct_m": 796.54369699,
                    },
                    "flows": {"CO2-C": 0.23985145},
                    "main_input": 2.946397,
                    "main_output": 0.99,
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.05644926,
                        "co2_bound_in_product_last_proc_e": 148.05644926,
                        "co2_bound_in_product_last_proc_m": 148.05644926,
                        "co2_bound_in_product_m": 148.05644926,
                    },
                    "main_input": 0.99,
                    "main_output": 0.99,
                    "process_code": "DRI-SB#B",
                    "process_step": "SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 14.65778518,
                        "co2_bound_in_product_last_proc_e": 148.05644926,
                        "co2_bound_in_product_last_proc_m": 148.05644926,
                        "co2_bound_in_product_m": 14.65778518,
                        "co2_direct_e": 133.39866408,
                        "co2_direct_m": 133.39866408,
                        "co2e_total_direct_e": 133.39866408,
                        "co2e_total_direct_m": 133.39866408,
                    },
                    "main_input": 0.99,
                    "main_output": 1.0,
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "emissions": {
                        "co2_direct_e": 0.23985145,
                        "co2_direct_m": 0.23985145,
                        "co2_in_flows_e": 0.23985145,
                        "co2_in_flows_m": 0.23985145,
                        "co2e_total_direct_e": 0.23985145,
                        "co2e_total_direct_m": 0.23985145,
                    },
                    "main_input": 0.23985145,
                    "main_output": 0.23985145,
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:CO2 transport and storage",
                },
                {
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:Electricity generation",
                },
            ],
            [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "Bound in product",
                    "values": 14657.78518,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CO2-T+S#B",
                    "values": 239.85144778,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "EAF#B",
                    "values": 133398.66407992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-DRI-C#B",
                    "values": 796543.69699477,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "NG-PROD#B",
                    "values": 21028.18077976,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-PROD#B",
                    "values": 8150.35505695,
                },
            ],
            [
                {
                    "process_subtype": "CO2-T+S#B",
                    "process_type": "CO2 transport and storage",
                    "values": 0.0072549,
                },
                {
                    "process_subtype": "DRI-SB#B",
                    "process_type": "Transportation (Ship)",
                    "values": 0.00478268,
                },
                {
                    "process_subtype": "EAF#B",
                    "process_type": "Derivative production",
                    "values": 0.18368496,
                },
                {
                    "process_subtype": "NG-DRI-C#B",
                    "process_type": "Derivative production",
                    "values": 9.15e-06,
                },
                {
                    "process_subtype": "NG-PROD#B",
                    "process_type": "Natural gas production",
                    "values": 0.01432705,
                },
            ],
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
                        "LOSS": 0.0139,
                        "OPEX-O": 0.00316265,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    }
                ],
                "main_import_process_chain": [
                    {
                        "CAPEX": 0.59187636,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "EL": 0.47685859, "IOP-S": 1.37373737},
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
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                ],
                "parameter": {
                    "SPECCOST": {"DIESEL-L": 0.04285714, "EL": 0.08078},
                    "WACC": 0.14554836,
                },
                "parameter_i": {
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.1,
                        "IOP-S": 0.26707598,
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
                        "process_code": "CCGT-CC#B",
                    },
                },
                "secondary_process_i": {
                    "CO2-C": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1.0, "EL": 100.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.14792048,
                        "process_code": "CO2-T+S#B",
                    }
                },
                "transport_process_chain": [
                    {
                        "CAPEX": 408.10708157,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"EL": 0.00274153},
                        "EFF": 0.85708919,
                        "EF_E": {"NG-G": 201.0, "NG-L": 201.0},
                        "EF_M": {"NG-G": 201.0, "NG-L": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "LOSS": 0.0005,
                        "OPEX-F": 8.16214163,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                    {
                        "CONV-OT": {"BFUEL-L": 3.3e-06, "NG-L": 1.15e-06},
                        "DIST": 3174.14,
                        "EFF": 1,
                        "EF_E": {"NG-L": 201.0},
                        "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                        "process_code": "CH4-SB#B",
                        "step": "SHP",
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
                        "LOSS_FLOW": {"NG-G": 4e-08},
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                ],
            },
            [
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 96.12405658,
                        "ch4_direct_co2e_m": 96.12405658,
                        "ch4_direct_e": 3.22563948,
                        "ch4_direct_m": 3.22563948,
                        "co2_bound_in_product_e": 690.97336284,
                        "co2_bound_in_product_m": 690.97336284,
                        "co2_direct_e": 63.21086003,
                        "co2_direct_m": 63.21086003,
                        "co2_in_flows_e": 754.18422287,
                        "co2_in_flows_m": 754.18422287,
                        "co2e_total_direct_e": 159.33491661,
                        "co2e_total_direct_m": 159.33491661,
                    },
                    "main_input": 3.80431534,
                    "main_output": 3.43767842,
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 3.1663146,
                        "ch4_direct_co2e_m": 3.1663146,
                        "ch4_direct_e": 0.10625217,
                        "ch4_direct_m": 0.10625217,
                        "co2_bound_in_product_e": 592.22579704,
                        "co2_bound_in_product_last_proc_e": 690.97336284,
                        "co2_bound_in_product_last_proc_m": 690.97336284,
                        "co2_bound_in_product_m": 592.22579704,
                        "co2_direct_e": 789.37561457,
                        "co2_direct_m": 789.37561457,
                        "co2_in_flows_e": 690.62804877,
                        "co2_in_flows_m": 690.62804877,
                        "co2e_total_direct_e": 792.54192918,
                        "co2e_total_direct_m": 792.54192918,
                    },
                    "main_input": 3.43767842,
                    "main_output": 2.946397,
                    "process_code": "CH4-LIQ#B",
                    "process_step": "PRE_SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 592.22579704,
                        "co2_bound_in_product_last_proc_e": 592.22579704,
                        "co2_bound_in_product_last_proc_m": 592.22579704,
                        "co2_bound_in_product_m": 592.22579704,
                        "co2_direct_e": 594.39463225,
                        "co2_direct_m": 603.42818167,
                        "co2_in_flows_e": 594.39463225,
                        "co2_in_flows_m": 603.42818167,
                        "co2e_total_direct_e": 594.39463225,
                        "co2e_total_direct_m": 603.42818167,
                    },
                    "flows": {"BFUEL-L": 0.03086494, "NG-L": 0.01079023},
                    "main_input": 2.946397,
                    "main_output": 2.946397,
                    "process_code": "CH4-SB#B",
                    "process_step": "SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 592.22579704,
                        "co2_bound_in_product_last_proc_e": 592.22579704,
                        "co2_bound_in_product_last_proc_m": 592.22579704,
                        "co2_bound_in_product_m": 592.22579704,
                        "co2_direct_e": 592.225797,
                        "co2_direct_m": 592.225797,
                        "co2_in_flows_e": 592.225797,
                        "co2_in_flows_m": 592.225797,
                        "co2e_total_direct_e": 592.225797,
                        "co2e_total_direct_m": 592.225797,
                    },
                    "main_input": 2.946397,
                    "main_output": 2.946397,
                    "process_code": "CH4-RGAS#B",
                    "process_step": "POST_SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.05644926,
                        "co2_bound_in_product_last_proc_e": 592.22579704,
                        "co2_bound_in_product_last_proc_m": 592.22579704,
                        "co2_bound_in_product_m": 148.05644926,
                        "co2_captured_e": 239.85144778,
                        "co2_captured_m": 239.85144778,
                        "co2_direct_e": 796.54369699,
                        "co2_direct_m": 796.54369699,
                        "co2_in_flows_e": 592.225797,
                        "co2_in_flows_m": 592.225797,
                        "co2e_total_direct_e": 796.54369699,
                        "co2e_total_direct_m": 796.54369699,
                    },
                    "flows": {"CO2-C": 0.23985145},
                    "main_input": 2.946397,
                    "main_output": 0.99,
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV_I",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 14.65778518,
                        "co2_bound_in_product_last_proc_e": 148.05644926,
                        "co2_bound_in_product_last_proc_m": 148.05644926,
                        "co2_bound_in_product_m": 14.65778518,
                        "co2_direct_e": 133.39866408,
                        "co2_direct_m": 133.39866408,
                        "co2e_total_direct_e": 133.39866408,
                        "co2e_total_direct_m": 133.39866408,
                    },
                    "main_input": 0.99,
                    "main_output": 1.0,
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:Electricity generation",
                },
            ],
            [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "Bound in product",
                    "values": 14657.78518,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "EAF#B",
                    "values": 133398.66407992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-DRI-C#B",
                    "values": 796543.69699477,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "NG-PROD#B",
                    "values": 96124.05658408,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-PROD#B",
                    "values": 63210.86002771,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "CH4-LIQ#B",
                    "values": 3166.31460453,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CH4-LIQ#B",
                    "values": 789375.61457463,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CH4-RGAS#B",
                    "values": 592225.797,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CH4-SB#B",
                    "values": 603428.18167276,
                },
            ],
            [
                {
                    "process_subtype": "CH4-LIQ#B",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02886908,
                },
                {
                    "process_subtype": "EAF#B",
                    "process_type": "Derivative production",
                    "values": 0.18368496,
                },
                {
                    "process_subtype": "NG-DRI-C#B",
                    "process_type": "Derivative production",
                    "values": 8.8e-06,
                },
                {
                    "process_subtype": "NG-PROD#B",
                    "process_type": "Natural gas production",
                    "values": 0.01087216,
                },
            ],
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data(
    api_kwargs, calculation_data_exp, values_exp, res_emission_mass_exp, res_costs_exp
):
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

    assert_deep_equal_approx(calculation_data_exp, calculation_data)
    assert_deep_equal_approx(values_exp, values)
    assert_deep_equal_approx(res_emission_mass_exp, res_emission_mass)
    assert_deep_equal_approx(res_costs_exp, res_costs)


@pytest.mark.parametrize(
    "api_kwargs,calculation_data_exp",
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
                "main_export_process_chain": [
                    {
                        "CBOUND": {"NG-G": 0.0548514},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV": {"DIESEL-L": 0.00059456},
                        "EFF": 0.98270994,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": 0.00378,
                        "OPEX-O": 0.00486257,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    {
                        "CAPEX": 0.59187636,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "EL": 0.47685859, "IOP-S": 1.37373737},
                        "EFF": 0.3360036,
                        "EF_E": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                        "EF_M": {"CH4-G": 201.0, "CO2-C": 1.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01775629,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV",
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
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    }
                ],
                "parameter": {
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.08078,
                        "IOP-S": 0.26707598,
                    },
                    "WACC": 0.0487,
                },
                "parameter_i": {
                    "SPECCOST": {"EL": 0.1, "NG-G": 0.03056527},
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
                        "process_code": "CCGT-CC#B",
                    },
                },
                "transport_process_chain": [
                    {
                        "DIST": 12830.0,
                        "EFF": 1,
                        "OPEX-T": 3.8e-07,
                        "process_code": "DRI-SB#B",
                        "step": "SHP",
                    }
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
                        "LOSS": 0.0139,
                        "OPEX-O": 0.00316265,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    }
                ],
                "main_import_process_chain": [
                    {
                        "CAPEX": 0.59187636,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "EL": 0.47685859, "IOP-S": 1.37373737},
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
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                ],
                "parameter": {
                    "SPECCOST": {"DIESEL-L": 0.04285714, "EL": 0.08078},
                    "WACC": 0.14554836,
                },
                "parameter_i": {
                    "SPECCOST": {
                        "DIESEL-L": 0.04285714,
                        "EL": 0.1,
                        "IOP-S": 0.26707598,
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
                        "process_code": "CCGT-CC#B",
                    },
                },
                "secondary_process_i": {
                    "CO2-C": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1.0, "EL": 100.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.14792048,
                        "process_code": "CO2-T+S#B",
                    }
                },
                "transport_process_chain": [
                    {
                        "CAPEX": 408.10708157,
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"EL": 0.00274153},
                        "EFF": 0.85708919,
                        "EF_E": {"NG-G": 201.0, "NG-L": 201.0},
                        "EF_M": {"NG-G": 201.0, "NG-L": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "LOSS": 0.0005,
                        "OPEX-F": 8.16214163,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                    {
                        "CONV-OT": {"BFUEL-L": 3.3e-06, "NG-L": 1.15e-06},
                        "DIST": 3174.14,
                        "EFF": 1,
                        "EF_E": {"NG-L": 201.0},
                        "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                        "process_code": "CH4-SB#B",
                        "step": "SHP",
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
                        "LOSS_FLOW": {"NG-G": 4e-08},
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                ],
            },
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data_2(api_kwargs, calculation_data_exp):
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

    calculation_data = chain_process.get_calculation_data(
        data_handler=data_handler,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
    )
    assert_deep_equal_approx(calculation_data_exp, calculation_data)
