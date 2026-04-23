"""Unittests for blue hydrogen version."""

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static import (
    TransportType,
)
from ptxboa.static._type_defs import ChainDef
from tests.test_api import ptxdata_dir_static
from tests.utils import assert_deep_equal_approx


def _translate_user_data_inplace(user_data: pd.DataFrame) -> None:
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
                "process_code": "NG-PROD#B",
                "flow_code": "NG-G",  # main flow in
                "parameter_code": "LOSS",
                "value": 0.05,  # process_calc!E9
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
    _translate_user_data_inplace(user_data)

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

    calculation_data = data_handler.get_calculation_data(
        ptx_calc=ptx_calc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=False,
    )
    ptxcalc_results = ptx_calc.calculate(data=calculation_data)

    expected = [
        {
            "emissions": {
                "emission": {
                    "ch4_direct_co2e": 288.09291729,
                    "co2_direct": 621.8363534,
                },
                "mass": {"ch4_direct_co2e": 288.09291729, "co2_direct": 621.8363534},
            },
            "flows": {"main_flow_in": 3.24839886, "main_flow_out": 3.0937132},
            "parameter": {
                "CH4SHARE": {"NG-G": 0.909},
                "EFF": 0.95238095,
                "EF_E": {"NG-G": 201.0},
                "EF_M": {"NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS": {"NG-G": 0.05},
                "process_code": "NG-PROD#B",
                "step": "NG_PROD",
            },
            "process_code": "NG-PROD#B",
            "process_step": "NG_PROD",
        },
        {
            "costs": {"CAPEX": 4.19e-06, "OPEX": 2.51e-06},
            "emissions": {
                "emission": {
                    "ch4_direct_co2e": 274.37420694,
                    "co2_bound_in_product": 148.05784985,
                    "co2_bound_in_product_per_output": 149.55338219,
                    "co2_captured": 239.85116488,
                    "co2_direct": 204.31608375,
                    "co2_indirect_scope2": 189.78034672,
                },
                "mass": {
                    "ch4_direct_co2e": 274.37420694,
                    "co2_bound_in_product": 148.05784985,
                    "co2_bound_in_product_per_output": 149.55338219,
                    "co2_captured": 239.85116488,
                    "co2_direct": 204.31608375,
                },
            },
            "flows": {
                "main_flow_in": 3.0937132,
                "main_flow_out": 0.99000001,
                "secondary_flows_in": {
                    "CO2-C": 0.23985116,
                    "EL": 0.47209041,
                    "IOP-S": 1.35999964,
                },
            },
            "parameter": {
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
            "process_code": "NG-DRI-C#B",
            "process_step": "DERIV",
        },
        {
            "emissions": {
                "emission": {
                    "co2_bound_in_product": 148.05784985,
                    "co2_bound_in_product_per_output": 149.55338219,
                },
                "mass": {
                    "co2_bound_in_product": 148.05784985,
                    "co2_bound_in_product_per_output": 149.55338219,
                },
            },
            "flows": {"main_flow_in": 0.99000001, "main_flow_out": 0.99000001},
            "parameter": {
                "DIST": 999.0,
                "DST-S-D": 999.0,
                "EFF": 1.0,
                "process_code": "DRI-SB#B",
                "step": "SHP",
            },
            "process_code": "DRI-SB#B",
            "process_step": "SHP",
        },
        {
            "costs": {"CAPEX": 2.98e-06, "OPEX": 0.18368079},
            "emissions": {
                "emission": {
                    "ch4_direct_co2e": 0.3724882,
                    "co2_direct": 148.05784985,
                    "co2_indirect_scope2": 195.3,
                },
                "mass": {"ch4_direct_co2e": 0.3724882, "co2_direct": 148.86184985},
            },
            "flows": {
                "main_flow_in": 0.99000001,
                "main_flow_out": 1,
                "secondary_flows_in": {"EL": 0.651, "NG-G": 0.0042},
            },
            "is_in_import_segment": True,
            "parameter": {
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
            },
            "process_code": "EAF#B",
            "process_step": "DERIV_I",
        },
        {"process_code": "DIESEL-L", "process_step": "MARKET:DIESEL-L"},
        {"process_code": "CO2-C", "process_step": "MARKET:CO2-C"},
        {
            "costs": {"FLOW": 0.03813546},
            "flows": {"main_flow_out": 0.47209041},
            "parameter": {"SPECCOST": {"EL": 0.08078}},
            "process_code": "EL",
            "process_step": "MARKET:EL",
        },
        {"process_code": "CH4-G", "process_step": "MARKET:CH4-G"},
        {
            "flows": {"main_flow_out": 1.35999964},
            "process_code": "IOP-S",
            "process_step": "MARKET:IOP-S",
        },
        {
            "flows": {"main_flow_out": 0.0042},
            "is_in_import_segment": True,
            "process_code": "NG-G",
            "process_step": "MARKET:IMPORT:NG-G",
        },
        {
            "costs": {"FLOW": 0.05258778},
            "flows": {"main_flow_out": 0.651},
            "is_in_import_segment": True,
            "parameter": {"SPECCOST": {"EL": 0.08078}},
            "process_code": "EL",
            "process_step": "MARKET:IMPORT:EL",
        },
    ]

    assert_deep_equal_approx(
        expected, ptxcalc_results._internal_process_data, sort_list_by_keys=["step"]
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
                "chain": "CHX-L__EFUELSYNC__prod_in_supply",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            [
                {
                    "costs": {"OPEX": 0.00880988},
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 12.93049073,
                            "co2_bound_in_product": 364.16703194,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 5.29911034,
                        },
                        "mass": {
                            "ch4_direct_co2e": 12.93049073,
                            "co2_bound_in_product": 364.16703194,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 5.29911034,
                        },
                    },
                    "flows": {
                        "main_flow_in": 1.84365315,
                        "main_flow_out": 1.81177628,
                        "secondary_flows_in": {"DIESEL-L": 0.00107721},
                    },
                    "parameter": {
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
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "costs": {"CAPEX": 0.0110973, "OPEX": 0.00298571},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                            "co2_captured": 82.61781001,
                            "co2_direct": 10.21119,
                        },
                        "mass": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                            "co2_captured": 82.61781001,
                            "co2_direct": 10.21119,
                        },
                    },
                    "flows": {
                        "main_flow_in": 1.789,
                        "main_flow_out": 1.0,
                        "secondary_flows_in": {"CO2-C": 0.08261781, "EL": 0.0115},
                    },
                    "parameter": {
                        "CAPEX": 1109.2414246,
                        "CBOUND": {"NG-G": 0.07279681},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"NG-G": 0.89},
                        "CO2CPT-S": {"NG-G": 0.25815306},
                        "CONV": {"EL": 0.0115},
                        "EFF": 0.55897149,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 25.0,
                        "OPEX-F": 20.9,
                        "WACC": 0.0487,
                        "process_code": "EFUELSYNC#B",
                        "step": "DERIV",
                    },
                    "process_code": "EFUELSYNC#B",
                    "process_step": "DERIV",
                },
                {
                    "costs": {"OPEX": 0.00057767},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                        },
                        "mass": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                            "co2_direct": 4.74715381,
                        },
                    },
                    "flows": {
                        "main_flow_in": 1.0,
                        "main_flow_out": 1,
                        "secondary_flows_in": {"BFUEL-L": 0.0162196},
                    },
                    "parameter": {
                        "CONV": {"BFUEL-L": 0.0162196},
                        "CONV-OT": {"BFUEL-L": 1.26e-06},
                        "DIST": 12830.0,
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 1.0,
                        "EF_M": {"BFUEL-L": 292.68},
                        "OPEX-T": 5e-08,
                        "process_code": "SYN-SB#B",
                        "step": "SHP",
                    },
                    "process_code": "SYN-SB#B",
                    "process_step": "SHP",
                },
                {
                    "costs": {"OPEX": 0.0026233},
                    "flows": {"main_flow_out": 0.08672787},
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.03024746,
                        "WACC": 0.0487,
                        "process_code": "CO2-T+S#B",
                        "step": "SECONDARY:CO2-C",
                    },
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:CO2-C",
                },
                {
                    "costs": {"CAPEX": 0.00025356, "OPEX": 0.00010475},
                    "emissions": {
                        "emission": {
                            "co2_captured": 4.11005532,
                            "co2_direct": 0.4679766,
                        },
                        "mass": {"co2_captured": 4.11005532, "co2_direct": 0.4679766},
                    },
                    "flows": {
                        "main_flow_in": 0.02277628,
                        "main_flow_out": 0.0115,
                        "secondary_flows_in": {"CO2-C": 0.00411006},
                    },
                    "parameter": {
                        "CAPEX": 2408.19070902,
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.75889534,
                        "WACC": 0.0487,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:EL",
                    },
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:EL",
                },
                {
                    "costs": {"FLOW": 4.617e-05},
                    "flows": {"main_flow_out": 0.00107721},
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.04285714}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:DIESEL-L",
                },
                {
                    "costs": {"FLOW": 5.23e-05},
                    "flows": {"main_flow_out": 0.0162196},
                    "parameter": {"SPECCOST": {"BFUEL-L": 0.00322434}},
                    "process_code": "BFUEL-L",
                    "process_step": "MARKET:BFUEL-L",
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
            [
                {
                    "costs": {"OPEX": 0.01087216},
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 96.12405658,
                            "co2_bound_in_product": 690.97336284,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 63.76324902,
                        },
                        "mass": {
                            "ch4_direct_co2e": 96.12405658,
                            "co2_bound_in_product": 690.97336284,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 63.76324902,
                        },
                    },
                    "flows": {
                        "main_flow_in": 3.80431534,
                        "main_flow_out": 3.43767842,
                        "secondary_flows_in": {"DIESEL-L": 0.00207073},
                    },
                    "parameter": {
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
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 3.1663146,
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 98.40225178,
                        },
                        "mass": {
                            "ch4_direct_co2e": 3.1663146,
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 98.40225178,
                        },
                    },
                    "flows": {
                        "main_flow_in": 3.43767842,
                        "main_flow_out": 2.946397,
                        "secondary_flows_in": {"EL": 0.00807763},
                    },
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"EL": 0.00274153},
                        "EFF": 0.85708919,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": {"NG-G": 0.0005},
                        "WACC": 0.14554836,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                    "process_code": "CH4-LIQ#B",
                    "process_step": "PRE_SHP",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                        "mass": {
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 9.03354942,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "secondary_flows_in": {"BFUEL-L": 0.03086494},
                    },
                    "parameter": {
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
                    },
                    "process_code": "CH4-SB#B",
                    "process_step": "SHP",
                },
                {
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 1.9e-07,
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.50496389,
                            "co2_indirect_scope2": 0.14142706,
                        },
                        "mass": {
                            "ch4_direct_co2e": 1.9e-07,
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.50496389,
                            "co2_indirect_scope2": 0.14142706,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "secondary_flows_in": {
                            "DIESEL-L": 5.89e-06,
                            "EL": 0.00141427,
                            "NG-G": 0.00250444,
                        },
                    },
                    "is_in_import_segment": True,
                    "parameter": {
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
                    "process_code": "CH4-RGAS#B",
                    "process_step": "POST_SHP",
                },
                {
                    "costs": {"CAPEX": 5.24e-06, "OPEX": 2.09e-06},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 148.05644926,
                            "co2_bound_in_product_per_output": 149.55196895,
                            "co2_captured": 239.8514478,
                            "co2_direct": 204.31789998,
                            "co2_indirect_scope2": 47.209,
                        },
                        "mass": {
                            "co2_bound_in_product": 148.05644926,
                            "co2_bound_in_product_per_output": 149.55196895,
                            "co2_captured": 239.8514478,
                            "co2_direct": 204.31789998,
                            "co2_indirect_scope2": 47.209,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 0.99,
                        "secondary_flows_in": {
                            "CO2-C": 0.23985145,
                            "EL": 0.47209,
                            "IOP-S": 1.36,
                        },
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 0.49319758,
                        "CBOUND": {"NG-G": 0.04081161},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"EL": 0.47685859, "IOP-S": 1.37373737},
                        "EFF": 0.3360036,
                        "EF_E": {
                            "CH4-G": 201.0,
                            "CO2-C": 1000.0,
                            "EL": 100.0,
                            "NG-G": 201.0,
                        },
                        "EF_M": {
                            "CH4-G": 201.0,
                            "CO2-C": 1000.0,
                            "EL": 100.0,
                            "NG-G": 201.0,
                        },
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01479593,
                        "WACC": 0.0423,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV_I",
                },
                {
                    "costs": {"CAPEX": 3.69e-06, "OPEX": 0.1516002},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 14.65778518,
                            "co2_bound_in_product_per_output": 14.65778518,
                            "co2_direct": 193.69866408,
                            "co2_indirect_scope2": 65.1,
                        },
                        "mass": {
                            "co2_bound_in_product": 14.65778518,
                            "co2_bound_in_product_per_output": 14.65778518,
                            "co2_direct": 193.69866408,
                            "co2_indirect_scope2": 65.1,
                        },
                    },
                    "flows": {
                        "main_flow_in": 0.99,
                        "main_flow_out": 1,
                        "secondary_flows_in": {"EL": 0.651, "NG-G": 0.3},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 0.344454,
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "EFF": 1.01010101,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01033362,
                        "OPEX-O": 0.15159873,
                        "WACC": 0.0423,
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "costs": {"OPEX": 0.09492721},
                    "flows": {"main_flow_out": 0.6417449},
                    "is_in_import_segment": True,
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.14792048,
                        "WACC": 0.0423,
                        "process_code": "CO2-T+S#B",
                        "step": "SECONDARY:IMPORT:CO2-C",
                    },
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:IMPORT:CO2-C",
                },
                {
                    "costs": {"CAPEX": 0.0230011, "OPEX": 0.01024245},
                    "emissions": {
                        "emission": {
                            "co2_captured": 401.89345705,
                            "co2_direct": 45.7601461,
                        },
                        "mass": {
                            "co2_captured": 401.89345705,
                            "co2_direct": 45.7601461,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.22713235,
                        "main_flow_out": 1.12450427,
                        "secondary_flows_in": {"CO2-C": 0.40189346},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 2408.19070902,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.75889534,
                        "WACC": 0.0423,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:IMPORT:EL",
                    },
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:IMPORT:EL",
                },
                {
                    "costs": {"FLOW": 0.06807291},
                    "flows": {"main_flow_out": 2.22713235},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03056527}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
                {
                    "costs": {"FLOW": 8.875e-05},
                    "flows": {"main_flow_out": 0.00207073},
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.04285714}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:DIESEL-L",
                },
                {
                    "costs": {"FLOW": 0.00065251},
                    "flows": {"main_flow_out": 0.00807763},
                    "parameter": {"SPECCOST": {"EL": 0.08078}},
                    "process_code": "EL",
                    "process_step": "MARKET:EL",
                },
                {
                    "costs": {"FLOW": 9.952e-05},
                    "flows": {"main_flow_out": 0.03086494},
                    "parameter": {"SPECCOST": {"BFUEL-L": 0.00322434}},
                    "process_code": "BFUEL-L",
                    "process_step": "MARKET:BFUEL-L",
                },
                {
                    "costs": {"FLOW": 7.655e-05},
                    "flows": {"main_flow_out": 0.00250444},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03056527}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
                {
                    "costs": {"FLOW": 2.5e-07},
                    "flows": {"main_flow_out": 5.89e-06},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.04285714}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:IMPORT:DIESEL-L",
                },
                {
                    "is_in_import_segment": True,
                    "process_code": "CH4-G",
                    "process_step": "MARKET:IMPORT:CH4-G",
                },
                {
                    "costs": {"FLOW": 0.36322333},
                    "flows": {"main_flow_out": 1.36},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"IOP-S": 0.26707598}},
                    "process_code": "IOP-S",
                    "process_step": "MARKET:IMPORT:IOP-S",
                },
                {
                    "costs": {"FLOW": 0.00916958},
                    "flows": {"main_flow_out": 0.3},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03056527}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
            ],
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data(api_kwargs, expected):
    """Data test for blue iron chain using current data."""
    # test api output

    # validate and translate user settings
    chain_def, tool_version_color, optimize_flh = _translate_and_validate_user_settings(
        **api_kwargs
    )

    data_handler = DataHandler(
        data_dir=DEFAULT_DATA_DIR,
        scenario=api_kwargs["scenario"],
        tool_version_color=tool_version_color,
    )
    ptx_calc = PtxCalc.get_or_create(chain_def)

    data = data_handler.get_calculation_data(
        ptx_calc=ptx_calc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=optimize_flh,
    )

    # calculate results
    ptxcalc_result = ptx_calc.calculate(data)  # NEW # noqa

    assert_deep_equal_approx(
        expected,
        ptxcalc_result._internal_process_data,
        allow_new_dict_items=True,
        sort_list_by_keys=[
            "step",
            "process_type",
            "process_subtype",
            "cost_type",
            "emissionemission_type",
            "gas_type",
        ],
    )


@pytest.mark.parametrize(
    "api_kwargs, expected",
    [
        [
            {
                "scenario": "2030 (high)",
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": None,
                "res_gen": None,
                "chain": "CH3OH-L__ATR_91%_CH3OHSYN__prod_in_demand",
                "region": "China",
                "country": "Japan",
                "transport": "Ship",
                "ship_own_fuel": False,
            },
            # DAC process in import region
            {
                "SECONDARY:IMPORT:CO2-G": {
                    "costs": {"CAPEX": 0.0070417, "OPEX": 0.0039147},
                    "emissions": {
                        "emission": {"co2_indirect_scope2": 91.02097751},
                        "mass": {
                            "co2_bound_in_product": 248.4875171,
                            "co2_bound_in_product_per_output": 1000.00000007,
                            "co2_indirect_scope2": 91.02097751,
                        },
                    },
                    "flows": {
                        "main_flow_in": 0.24848752,
                        "main_flow_out": 0.24848752,
                        "secondary_flows_in": {"EL": 0.05590969, "HEAT": 0.37273128},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 0.39385297,
                        "CBOUND": {"CO2-DAC": 0.27289252},
                        "CONV": {"EL": 0.225, "HEAT": 1.5},
                        "EFF": 1.0,
                        "EF_E": {"EL": 288.0, "HEAT": 201.0},
                        "EF_M": {"CO2-DAC": 1000.0, "EL": 288.0, "HEAT": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 25.0,
                        "OPEX-F": 0.01575412,
                        "WACC": 0.0514,
                        "process_code": "DAC#B",
                        "step": "SECONDARY:IMPORT:CO2-G",
                    },
                    "process_code": "DAC#B",
                    "process_step": "SECONDARY:IMPORT:CO2-G",
                },
                "DERIV_I": {
                    "costs": {"CAPEX": 0.00739343, "OPEX": 0.00335591},
                    "emissions": {
                        "emission": {"co2_indirect_scope2": 15.46211741},
                        "mass": {
                            "co2_bound_in_product": 248.49429268,
                            "co2_bound_in_product_per_output": 248.49429268,
                            "co2_indirect_scope2": 15.46211741,
                        },
                    },
                    "flows": {
                        "main_flow_in": 1.16206724,
                        "main_flow_out": 1,
                        "secondary_flows_in": {"CO2-G": 0.24848752, "EL": 0.05368791},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 783.04495615,
                        "CBOUND": {"CO2-G": 0.06781223},
                        "CONV": {
                            "CO2-G": 0.24848752,
                            "EL": 0.05368791,
                            "HEAT": -0.08630206,
                        },
                        "EFF": 0.86053541,
                        "EF_E": {"CO2-G": 1000.0, "EL": 288.0, "HEAT": 201.0},
                        "EF_M": {"CO2-G": 1000.0, "EL": 288.0, "HEAT": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 23.49134868,
                        "WACC": 0.0514,
                        "process_code": "CH3OHSYN#B",
                        "step": "DERIV_I",
                    },
                    "process_code": "CH3OHSYN#B",
                    "process_step": "DERIV_I",
                },
            },
        ],
    ],
)
def test_new_blue_chain_dac(api_kwargs, expected):

    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    result = api.calculate(**api_kwargs)

    # only compare partial results
    actual_step_data = {
        x["process_step"]: x for x in result._internal_process_data or []
    }
    for step, expected_step_data in expected.items():
        assert_deep_equal_approx(
            expected_step_data, actual_step_data[step], context=step
        )


def test_overall_sums():
    """Create one instance of each blue chain andcheck expected results (totals)."""
    df_chains = DataHandler.get_dimension(dim="chain", tool_version_color="blue")
    df_process = DataHandler.get_dimension(dim="process")

    flows_own_fuel = set(
        df_process.loc[df_process["is_shipping_own_fuel"], "main_flow_code_out"]
    )

    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    actual_results = {}

    for chain_name, chain in df_chains.iterrows():
        transport: TransportType = "Pipeline" if chain["can_pipeline"] else "Ship"
        ship_own_fuel: bool = (
            transport == "Ship" and chain["flow_out"] in flows_own_fuel
        )

        result = api.calculate(
            scenario="2030 (medium)",
            secproc_co2="Direct Air Capture (blue)",
            secproc_water=None,
            chain=chain_name,  # type: ignore
            res_gen=None,
            region="Algeria",
            country="Germany",
            transport=transport,
            ship_own_fuel=ship_own_fuel,
            output_unit="USD/t",
            optimize_flh=False,
            tool_version_color="blue",
        )

        actual_results[chain_name] = {
            "costs": result.costs[["process_type", "cost_type", "values"]]  # type: ignore # noqa
            .groupby(["process_type", "cost_type"])
            .sum(numeric_only=True)
            .reset_index()
            .to_dict(orient="records"),
            "emissions_t_co2e": result.emissions_t_co2e[  # type: ignore
                [
                    "process_type",
                    "emission_type",
                    "gas_type",
                    "values",
                ]
            ]
            .groupby(["process_type", "emission_type", "gas_type"])
            .sum(numeric_only=True)
            .reset_index()
            .to_dict(orient="records"),
            "emission_mass_t_co2e": result.emission_mass_t_co2e[  # type: ignore
                [
                    "process_type",
                    "emission_type",
                    "gas_type",
                    "values",
                ]
            ]
            .groupby(["process_type", "emission_type", "gas_type"])
            .sum(numeric_only=True)
            .reset_index()
            .to_dict(orient="records"),
        }

    expected_results = {
        "B-DRI-S__ATR_91%_DRI-rotary__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 97.077724,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00100117,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 13.57049583,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 40.35272279,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 6.04297702,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 19.35570062,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 18.0856384,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.05952485,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 7.25341711,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 3.72520235,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02699818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04145625,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.019745,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.06447374,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.04276822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00283481,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02699818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04145625,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.019745,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.06447374,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.04276822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00283481,
                },
            ],
        },
        "B-DRI-S__ATR_91%_DRI-rotary__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 76.50018009,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00207783,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 33.7940395,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 6.04297702,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 44.44738992,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 18.0856384,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.09308228,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 11.34256781,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02699818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04145625,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10082114,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06687903,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02699818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04145625,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10082114,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06687903,
                },
            ],
        },
        "B-DRI-S__ATR_91%_DRI__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 95.79843051,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00498912,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 6.96903103,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 20.72285203,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 3.1033276,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 24.28260623,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 22.68925545,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.07467663,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 9.09974146,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 4.67343567,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01386472,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05200875,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.024771,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08088524,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05365468,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0035564,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01386472,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05200875,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.024771,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08088524,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05365468,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0035564,
                },
            ],
        },
        "B-DRI-S__ATR_91%_DRI__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 75.49205816,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01035444,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 17.35468716,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 3.1033276,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 55.76127099,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 22.68925545,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.09164002,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 11.16681988,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01386472,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05200875,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09925896,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06584277,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01386472,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05200875,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09925896,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06584277,
                },
            ],
        },
        "B-DRI-S__NG-DRI-C__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 61.04701666,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00529047,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 366.89225331,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.0021137,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 9.75387362,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 29.00375661,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.34342524,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.07730417,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 9.41992128,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 4.83787329,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.14955197,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.20638172,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04768586,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0194051,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08373123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05554255,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00368153,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.14955197,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.20638172,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04768586,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0194051,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08373123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05554255,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00368153,
                },
            ],
        },
        "B-DRI-S__NG-DRI-C__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 48.1068939,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01097985,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 366.89225331,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.0021137,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 24.28966446,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.34342524,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.10121262,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.33329286,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.14955197,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.20638172,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0194051,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10962744,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07272063,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.14955197,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.20638172,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0194051,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10962744,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07272063,
                },
            ],
        },
        "B-DRI-S__SMR_52%_BF_DRI-rotary__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 78.09936219,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00100117,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 11.01675945,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 32.75902705,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.90579158,
                },
                {"cost_type": "CAPEX", "process_type": "H2 production", "values": 0.0},
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.08333479,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 10.15478395,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 5.21528329,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00726,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09026324,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05987551,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00396874,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00726,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09026324,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05987551,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00396874,
                },
            ],
        },
        "B-DRI-S__SMR_52%_BF_DRI-rotary__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 61.54465748,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00207783,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 27.43457634,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.90579158,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11036313,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.44833047,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11953872,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07929521,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11953872,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07929521,
                },
            ],
        },
        "B-DRI-S__SMR_52%_BF_DRI__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 71.98921297,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00498912,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 3.76525265,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 11.19621556,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.67667678,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.10454728,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.73963804,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 6.54280994,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.009108,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11323933,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07511655,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00497896,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.009108,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11323933,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07511655,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00497896,
                },
            ],
        },
        "B-DRI-S__SMR_52%_BF_DRI__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 56.72967525,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01035444,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 9.37645156,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.67667678,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11331963,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.80859486,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.12274101,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08141943,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.12274101,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08141943,
                },
            ],
        },
        "B-DRI-S__SMR_52%_DRI-rotary__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 78.09936219,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00100117,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 11.01675945,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 32.75902705,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.90579158,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 12.98286782,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 29.17816328,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.08333479,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 10.15478395,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 5.21528329,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00726,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09026324,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05987551,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00396874,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0466,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00726,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09026324,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05987551,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00396874,
                },
            ],
        },
        "B-DRI-S__SMR_52%_DRI-rotary__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 61.54465748,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00207783,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00053333,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 27.43457634,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.90579158,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 29.81315942,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 29.17816328,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11036313,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.44833047,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11953872,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07929521,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02191758,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30938646,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11953872,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07929521,
                },
            ],
        },
        "B-DRI-S__SMR_52%_DRI__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 71.98921297,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00498912,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 3.76525265,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 11.19621556,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.67667678,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 16.28759781,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 36.60533212,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.10454728,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.73963804,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 6.54280994,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.009108,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11323933,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07511655,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00497896,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0093,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.009108,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11323933,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07511655,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00497896,
                },
            ],
        },
        "B-DRI-S__SMR_52%_DRI__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 56.72967525,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01035444,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 374.98546478,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 0.00199331,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 9.37645156,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.67667678,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 37.40196363,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 36.60533212,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11331963,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.80859486,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.03568914,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.12274101,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08141943,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00749088,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38813938,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.12274101,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08141943,
                },
            ],
        },
        "CH3OH-L__ATR_91%_CH3OHSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 321.82514502,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 35.47677832},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 36.76494437,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 40.45313517,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 120.28994148,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 18.01388609,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 67.82545642,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 63.37495621,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 8.72662637},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.20858454,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 25.41712829,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 13.05370208,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.08048055,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.1452693,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06918962,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.22592625,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.14986666,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00993363,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.08048055,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.1452693,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06918962,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.22592625,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.14986666,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00993363,
                },
            ],
        },
        "CH3OH-L__ATR_91%_CH3OHSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 253.60793946,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 81.46696573},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 91.55420682,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 100.73875447,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 18.01388609,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 155.75073036,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 63.37495621,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 18.11126839},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.3084275,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 37.58351957,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.17260673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.90341328,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.08048055,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.1452693,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.33407014,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.22160319,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01566788,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.08048055,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.1452693,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.33407014,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.22160319,
                },
            ],
        },
        "CH3OH-L__CH3OHSYC__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 69.07371135,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 20.2014645,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 9.25760488,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 3.56162874,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 10.59072704,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.58600252,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.23561666,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 28.71113499,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 14.74543459,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04493294,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0174125,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00708578,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.25520582,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.16928907,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01122101,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04493294,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0174125,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00708578,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.25520582,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.16928907,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01122101,
                },
            ],
        },
        "CH3OH-L__CH3OHSYC__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 54.43217187,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 46.38955662,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 9.25760488,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 8.86937543,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.58600252,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.24307832,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 29.62037708,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.17260673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.90341328,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04493294,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00708578,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.26328784,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.17465022,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01566788,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04493294,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00708578,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.26328784,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.17465022,
                },
            ],
        },
        "CH3OH-L__SMR_52%_BF_CH3OHSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 255.32194387,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 35.47677832},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 36.76494437,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 31.50443632,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 93.68042267,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 14.02900726,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 2e-08},
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 8.72662637},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.29201836,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 35.58397961,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 18.27518292,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0254402,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.31629675,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.20981333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01390708,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0254402,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.31629675,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.20981333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01390708,
                },
            ],
        },
        "CH3OH-L__SMR_52%_BF_CH3OHSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 201.2014073,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 81.46696573},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 91.55420682,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 78.45418313,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 14.02900726,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 2e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 2e-08},
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 18.11126839},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.36898234,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 44.9624472,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.17260673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.90341328,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.39965951,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.26511146,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01566788,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.39965951,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.26511146,
                },
            ],
        },
        "CH3OH-L__SMR_52%_CH3OHSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 255.32194387,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 35.47677832},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 36.76494437,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 31.50443632,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 93.68042267,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 14.02900726,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 45.49403572,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 102.24492935,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 8.72662637},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.29201836,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 35.58397961,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 18.27518292,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0254402,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.31629675,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.20981333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01390708,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 0.44504114,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.02967748,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0254402,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.0679992,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.31629675,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.20981333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.01390708,
                },
            ],
        },
        "CH3OH-L__SMR_52%_CH3OHSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 201.2014073,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 81.46696573},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 21.63960192},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 91.55420682,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 18.55070789,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 78.45418313,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 14.02900726,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 104.47005688,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 102.24492935,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 18.11126839},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 3.04507356},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.36898234,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 44.9624472,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.17260673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.90341328,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.39965951,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.26511146,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01566788,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 1.37362123,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.06267733,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.0841394,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.39965951,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.26511146,
                },
            ],
        },
        "CHX-L__ATR_91%_EFUELSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 800.11975718,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 93.76993591},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 129.80229149,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 99.40427192,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 295.58485395,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 44.26498028,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 169.5712949,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 158.44454215,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 23.06565688},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.5214849,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 63.54568896,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 32.63572827,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.19776245,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.36318964,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.17298187,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.56484112,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.37468357,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0248352,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.19776245,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.36318964,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.17298187,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.56484112,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.37468357,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0248352,
                },
            ],
        },
        "CHX-L__ATR_91%_EFUELSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 630.51854734,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Carbon",
                    "values": 215.32823773,
                },
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 323.24123003,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 247.54231037,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 44.26498028,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 389.39440181,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 158.44454215,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 47.87053833},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.76677132,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 93.43513553,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.15454187,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.70705707,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.19776245,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.36318964,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.83052065,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.55092031,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01402809,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.19776245,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.36318964,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.83052065,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.55092031,
                },
            ],
        },
        "CHX-L__EFUELSYNC__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 153.23321337,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 124.12203663,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 35.66269841,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 2.80964411,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 8.35465346,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.25114182,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.55503854,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 67.6343779,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 34.73559285,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.12196699,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.01373611,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00558972,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.60118441,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.39879165,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.02643316,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.12196699,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.01373611,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00558972,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.60118441,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.39879165,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.02643316,
                },
            ],
        },
        "CHX-L__EFUELSYNC__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 120.75240266,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 285.02716945,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 35.66269841,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 6.99673949,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.25114182,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.55866671,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 68.07648953,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.15454187,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.70705707,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.12196699,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00558972,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.60511423,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.40139847,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01402809,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.12196699,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00558972,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.60511423,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.40139847,
                },
            ],
        },
        "CHX-L__SMR_52%_BF_EFUELSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 633.85424965,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 93.76993591},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 129.80229149,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 77.03151496,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 229.05805414,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 34.30233354,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 2e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 5e-08},
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 23.06565688},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.73007886,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 88.96396455,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 45.69001958,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06360336,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.79077757,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.524557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.03476928,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06360336,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.79077757,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.524557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.03476928,
                },
            ],
        },
        "CHX-L__SMR_52%_BF_EFUELSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 499.49630306,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Carbon",
                    "values": 215.32823773,
                },
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 323.24123003,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 191.8283673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 34.30233354,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 5e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 5e-08},
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 47.87053833},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.91816527,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 111.88328729,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.15454187,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.70705707,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.99450148,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.65969589,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01402809,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.99450148,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.65969589,
                },
            ],
        },
        "CHX-L__SMR_52%_EFUELSYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 633.85424965,
                },
                {"cost_type": "CAPEX", "process_type": "Carbon", "values": 93.76993591},
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 129.80229149,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 77.03151496,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 229.05805414,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 34.30233354,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 113.74022313,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 255.62386134,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 23.06565688},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.73007886,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 88.96396455,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 45.69001958,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06360336,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.79077757,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.524557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.03476928,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Carbon",
                    "values": 1.17630409,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.05157828,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06360336,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Heat",
                    "values": 0.1797311,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.79077757,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.524557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.03476928,
                },
            ],
        },
        "CHX-L__SMR_52%_EFUELSYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 499.49630306,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Carbon",
                    "values": 215.32823773,
                },
                {"cost_type": "OPEX", "process_type": "Carbon", "values": 57.19640231},
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 323.24123003,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 65.49511862,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 191.8283673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 34.30233354,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 261.18693128,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 255.62386134,
                },
                {"cost_type": "CAPEX", "process_type": "Heat", "values": 47.87053833},
                {"cost_type": "OPEX", "process_type": "Heat", "values": 8.04854234},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.91816527,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 111.88328729,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 0.15454187,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.70705707,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.44426818,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.99450148,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.65969589,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.01402809,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 3.1863,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.15325238,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 2.71047085,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.99450148,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.65969589,
                },
            ],
        },
        "H2-G__ATR_91%__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 1317.12860254,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 73.4314267,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 218.35296528,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 32.69920489,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 351.92182943,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 328.82978908,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.08226996,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 131.88031102,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 67.73095178,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.14609009,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.75375,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.359,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.17224982,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.77760407,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.05154203,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.14609009,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.75375,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.359,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.17224982,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.77760407,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.05154203,
                },
            ],
        },
        "H2-G__ATR_91%__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 1122.23426204,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 228.31798648,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 40.82732829,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 850.99880399,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 346.27132605,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.36188323,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 165.95266503,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Pipeline)",
                    "values": 957.93728021,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.18240406,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.79372983,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.47511013,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.97850442,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.18240406,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.79372983,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.47511013,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.97850442,
                },
            ],
        },
        "H2-G__ATR_91%__prod_in_supply__transport_NH3-L": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 1896.11602845,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 591.24480137,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 119.79798616,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 656.5511038,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 117.40304767,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1236.37243606,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 503.07981741,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 2.30467525,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 280.83685218,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 147.08772844,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 25.56411,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 104.63710736,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.52452105,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.15316928,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 2.49628582,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.65589448,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.52452105,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.15316928,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 2.49628582,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.65589448,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
        },
        "H2-G__SMR_52%_BF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 972.06747877,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 26.99985606,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 80.28576996,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 12.02310598,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 5e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-07},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.51517795,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 184.63243542,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 94.82333249,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05371557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.62520833,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.132,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.64114975,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.0886457,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.07215885,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05371557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.62520833,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.132,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.64114975,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.0886457,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.07215885,
                },
            ],
        },
        "H2-G__SMR_52%_BF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 835.89277212,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 106.55840622,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 19.05454362,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1.1e-07,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 1.1e-07,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.69274589,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 206.27002709,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Pipeline)",
                    "values": 957.93728021,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0851299,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.92357631,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.83348069,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.21622713,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0851299,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.92357631,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.83348069,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.21622713,
                },
            ],
        },
        "H2-G__SMR_52%_BF__prod_in_supply__transport_NH3-L": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 1480.10519063,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 591.24480137,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 119.79798616,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 479.65286594,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 85.77048757,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1.6e-07,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 1.6e-07,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 2.78536861,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 339.41187592,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 147.08772844,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 25.56411,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 104.63710736,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.38319641,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 8.60605966,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 3.01694399,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 2.00126959,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.38319641,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 8.60605966,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 3.01694399,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 2.00126959,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
        },
        "H2-G__SMR_52%__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 972.06747877,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 26.99985606,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 80.28576996,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 12.02310598,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 236.05214212,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 530.51205972,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.51517795,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 184.63243542,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 94.82333249,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05371557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.62520833,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.132,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.64114975,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.0886457,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.07215885,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05371557,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.62520833,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.132,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.64114975,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.0886457,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.07215885,
                },
            ],
        },
        "H2-G__SMR_52%__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 835.89277212,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 106.55840622,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 19.05454362,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 570.80883829,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 558.65107269,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 1.69274589,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 206.27002709,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Pipeline)",
                    "values": 957.93728021,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0851299,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.92357631,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.83348069,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.21622713,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0851299,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 5.92357631,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 1.83348069,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 1.21622713,
                },
            ],
        },
        "H2-G__SMR_52%__prod_in_supply__transport_NH3-L": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 1480.10519063,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 591.24480137,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 119.79798616,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 479.65286594,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 85.77048757,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 829.29883171,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 811.63543875,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 2.78536861,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 339.41187592,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 147.08772844,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Ship)",
                    "values": 25.56411,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 104.63710736,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.38319641,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 8.60605966,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 3.01694399,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 2.00126959,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.38319641,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 8.60605966,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 3.01694399,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 2.00126959,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Ship)",
                    "values": 0.02556411,
                },
            ],
        },
        "NH3-L__ATR_91%_NH3SYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 280.27474668,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 27.65571398,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 30.7104426,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 91.31943242,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 13.6754398,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 62.71535406,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 58.60016322,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.19286938,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 23.5021522,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 12.07021067,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0610977,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.13432443,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06397674,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.20890453,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.13857542,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00918521,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0610977,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.13432443,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.06397674,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.20890453,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.13857542,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00918521,
                },
            ],
        },
        "NH3-L__ATR_91%_NH3SYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 220.86496996,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 68.86987048,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 76.47693371,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 13.6754398,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 144.01616613,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 58.60016322,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.26845511,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 32.71267264,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 5.34319086,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0610977,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.13432443,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29077445,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19288328,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0610977,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.13432443,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29077445,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19288328,
                },
            ],
        },
        "NH3-L__SMR_52%_BF_NH3SYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 218.7820266,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 27.65571398,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 22.4359562,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 66.71472673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 9.99078953,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 2e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.27001713,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 32.90301308,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 16.89829494,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02352348,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29246634,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19400558,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0128593,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02352348,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29246634,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19400558,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0128593,
                },
            ],
        },
        "NH3-L__SMR_52%_BF_NH3SYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 172.40684829,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 68.86987048,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 55.87132551,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 9.99078953,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 2e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 2e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.32444763,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 39.53565745,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 5.34319086,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.35142219,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.23311355,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.35142219,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.23311355,
                },
            ],
        },
        "NH3-L__SMR_52%_NH3SYN__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 218.7820266,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 27.65571398,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 22.4359562,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 66.71472673,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 9.99078953,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 42.06642621,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 94.54159667,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.27001713,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 32.90301308,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 16.89829494,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02352348,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29246634,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19400558,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0128593,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.086164,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02352348,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.29246634,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.19400558,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.0128593,
                },
            ],
        },
        "NH3-L__SMR_52%_NH3SYN__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 172.40684829,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 68.86987048,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 13.95440902,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 55.87132551,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 9.99078953,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 96.59907875,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 94.54159667,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.32444763,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 39.53565745,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 5.34319086,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.35142219,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.23311355,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0446358,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 1.00245822,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.35142219,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.23311355,
                },
            ],
        },
        "STL-S__ATR_91%_DRI-rotary_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 130.52284528,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00468607,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 9.21299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 26.75062898,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 79.54467757,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 11.91212451,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 19.16214361,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 17.90478202,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.0589296,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 7.18088293,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 3.68795032,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05321974,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04104169,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.01954755,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.063829,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.04234054,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00280646,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.05321974,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04104169,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.01954755,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.063829,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.04234054,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00280646,
                },
            ],
        },
        "STL-S__ATR_91%_DRI-rotary_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 75.73517829,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00575196,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 74.31299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 33.4560991,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 5.98254725,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 44.00291602,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 17.90478202,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.09215146,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 11.22914213,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0267282,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04104169,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09981293,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06621024,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.0267282,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.04104169,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09981293,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06621024,
                },
            ],
        },
        "STL-S__ATR_91%_DRI_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 129.25634472,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00863415,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 380.44860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 20.21517882,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 60.11110552,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 9.00187159,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 24.03978017,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 22.46236289,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.07392986,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 9.00874405,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 4.62670132,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04021762,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05148866,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02452329,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08007639,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05311813,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00352084,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04021762,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05148866,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.02452329,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08007639,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05311813,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00352084,
                },
            ],
        },
        "STL-S__ATR_91%_DRI_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 74.73713757,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01394581,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 445.54860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 17.18114029,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 3.07229433,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 55.20365828,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 22.46236289,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.09072362,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 11.05515168,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01372608,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05148866,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09826637,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06518434,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01372608,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.05148866,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.09826637,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.06518434,
                },
            ],
        },
        "STL-S__NG-DRI-C_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 94.85244501,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00893248,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 372.43632889,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60229424,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 22.97217298,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 68.30920105,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 10.22956825,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.07653113,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 9.32572207,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 4.78949455,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.39801656,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.112309,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04570259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08289392,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05498713,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00364472,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.39801656,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.112309,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04570259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.08289392,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05498713,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00364472,
                },
            ],
        },
        "STL-S__NG-DRI-C_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 47.62582496,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01456497,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 437.53632889,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60229424,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 24.04676781,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.29999099,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.1002005,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.20995993,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.39801656,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01921105,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10853116,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07199342,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.39801656,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.01921105,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.10853116,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07199342,
                },
            ],
        },
        "STL-S__SMR_52%_BF_DRI-rotary_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 111.73426709,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00468607,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 9.21299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 24.22242995,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 72.02691878,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 10.78631093,
                },
                {"cost_type": "CAPEX", "process_type": "H2 production", "values": 0.0},
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.08250144,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 10.05323611,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 5.16313045,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04818995,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0071874,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.0893606,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05927676,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00392905,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04818995,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0071874,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.0893606,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05927676,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00392905,
                },
            ],
        },
        "STL-S__SMR_52%_BF_DRI-rotary_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 60.92921091,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00575196,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 74.31299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 27.16023058,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.85673366,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.1092595,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.31384717,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02169841,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11834333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07850225,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02169841,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11834333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07850225,
                },
            ],
        },
        "STL-S__SMR_52%_BF_DRI_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 105.68521936,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00863415,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 380.44860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 17.04343823,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 50.67973541,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 7.58948728,
                },
                {"cost_type": "CAPEX", "process_type": "H2 production", "values": 0.0},
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.10350181,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.61224166,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 6.47738184,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.03390752,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00901692,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11210694,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07436539,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00492917,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.03390752,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00901692,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11210694,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07436539,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00492917,
                },
            ],
        },
        "STL-S__SMR_52%_BF_DRI_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 56.16237849,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01394581,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 445.54860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 9.28268705,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.65991001,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 1e-08,
                },
                {"cost_type": "OPEX", "process_type": "H2 production", "values": 1e-08},
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11218643,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.67050891,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00741597,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.1215136,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08060523,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00741597,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.1215136,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08060523,
                },
            ],
        },
        "STL-S__SMR_52%_DRI-rotary_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 111.73426709,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00468607,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 9.21299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 24.22242995,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 72.02691878,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 10.78631093,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 12.85303914,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 28.88638165,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.08250144,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 10.05323611,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 5.16313045,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04818995,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0071874,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.0893606,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05927676,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00392905,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.111234,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.04818995,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.0071874,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.0893606,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.05927676,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00392905,
                },
            ],
        },
        "STL-S__SMR_52%_DRI-rotary_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 60.92921091,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00575196,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 74.31299812,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60072967,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 27.16023058,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 4.85673366,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 29.51502782,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 28.88638165,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.1092595,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.31384717,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02169841,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11834333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07850225,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.02169841,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.30629259,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11834333,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07850225,
                },
            ],
        },
        "STL-S__SMR_52%_DRI_EAF__prod_in_demand": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 105.68521936,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.00863415,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 380.44860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 17.04343823,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Electricity generation",
                    "values": 50.67973541,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 7.58948728,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 16.12472183,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 36.2392788,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.10350181,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 12.61224166,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Transportation (Pipeline)",
                    "values": 6.47738184,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.03390752,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00901692,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11210694,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07436539,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00492917,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.074307,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.03390752,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.00901692,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.11210694,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.07436539,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Transportation (Pipeline)",
                    "values": 0.00492917,
                },
            ],
        },
        "STL-S__SMR_52%_DRI_EAF__prod_in_supply": {
            "costs": [
                {
                    "cost_type": "OPEX",
                    "process_type": "CO2 transport and storage",
                    "values": 56.16237849,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Derivative production",
                    "values": 0.01394581,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Derivative production",
                    "values": 445.54860825,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Derivative production",
                    "values": 151.60217504,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "Electricity generation",
                    "values": 9.28268705,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Electricity generation",
                    "values": 1.65991001,
                },
                {
                    "cost_type": "CAPEX",
                    "process_type": "H2 production",
                    "values": 37.02794399,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "H2 production",
                    "values": 36.2392788,
                },
                {
                    "cost_type": "FLOW",
                    "process_type": "Natural gas production",
                    "values": 0.11218643,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Natural gas production",
                    "values": 13.67050891,
                },
                {
                    "cost_type": "OPEX",
                    "process_type": "Transportation (Ship)",
                    "values": 1.02533225,
                },
            ],
            "emission_mass_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00741597,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.1215136,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08060523,
                },
            ],
            "emissions_t_co2e": [
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Bound in product",
                    "values": 0.01465779,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.04564221,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_type": "Derivative production",
                    "values": 0.0651,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Electricity generation",
                    "values": 0.00741597,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "H2 production",
                    "values": 0.38425798,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_type": "Natural gas production",
                    "values": 0.1215136,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_type": "Natural gas production",
                    "values": 0.08060523,
                },
            ],
        },
    }

    assert_deep_equal_approx(
        expected_results,
        actual_results,
        sort_list_by_keys=["process_type", "cost_type", "emission_type", "gas_type"],
    )
