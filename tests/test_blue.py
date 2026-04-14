"""Unittests for blue hydrogen version."""

import pandas as pd
import pytest

from ptxboa.api import _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
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
                "emission": {"co2_direct": 621.8363534},
                "mass": {"co2_direct": 621.8363534},
            },
            "flows": {"main_flow_out": 3.0937132},
            "parameter": {
                "CH4SHARE": {"NG-G": 0.909},
                "EFF": 1.0,
                "EF_E": {"NG-G": 201.0},
                "EF_M": {"NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
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
                    "co2_indirect_scope2": 189.78034672,
                },
                "mass": {"ch4_direct_co2e": 274.37420694},
            },
            "flows": {
                "main_flow_in": 3.0937132,
                "main_flow_out": 0.99000001,
                "secondary_flows_in": {"EL": 0.47209041, "IOP-S": 1.35999964},
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
                    "co2_indirect_scope2": 195.3,
                },
                "mass": {"ch4_direct_co2e": 0.3724882, "co2_direct": 0.804},
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
                            "co2_bound_in_product": 364.16703194,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.2873553,
                        },
                        "mass": {
                            "co2_bound_in_product": 364.16703194,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.2873553,
                        },
                    },
                    "flows": {
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
                    "costs": {"CAPEX": 0.00952357, "OPEX": 0.00298571},
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
                        "CAPEX": 951.9379845,
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
                    "flows": {"main_flow_out": 0.08672787},
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
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
                    "parameter": {"SPECCOST": {"EL": 0.08078}},
                    "process_code": "EL",
                    "process_step": "MARKET:EL",
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
                            "co2_bound_in_product": 690.97336284,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.55238894,
                        },
                        "mass": {
                            "co2_bound_in_product": 690.97336284,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.55238894,
                        },
                    },
                    "flows": {
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
                    "costs": {"CAPEX": 0.02543352, "OPEX": 0.00343556},
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
                    "costs": {"CAPEX": 6.29e-06, "OPEX": 2.51e-06},
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
                        "CAPEX": 0.59187636,
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
                        "OPEX-F": 0.01775629,
                        "WACC": 0.0423,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV_I",
                },
                {
                    "costs": {"CAPEX": 4.48e-06, "OPEX": 0.18368048},
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
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "costs": {"OPEX": 0.09492721},
                    "flows": {"main_flow_out": 0.6417449},
                    "is_in_import_segment": True,
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1000.0, "EL": 100.0},
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
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"EL": 0.1}},
                    "process_code": "EL",
                    "process_step": "MARKET:IMPORT:EL",
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
