"""Unittests for blue hydrogen version."""

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static import SecProcCO2Values, TransportType
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
            "parameter": {"SPECCOST": {"BFUEL-L": 0.00322434}},
            "process_code": "BFUEL-L",
            "process_step": "MARKET:BFUEL-L",
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
                "chain": "CHX-L__EFUELSYNC__prod_in_demand",
                "res_gen": None,
                "transport": "Pipeline",
                "ship_own_fuel": False,
                "secproc_co2": "CO2 from fossil source",
                "secproc_water": "Sea Water desalination",
            },
            [
                {
                    "costs": {"OPEX": 0.01215573},
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 14.68312917,
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 6.01736804,
                        },
                        "mass": {
                            "ch4_direct_co2e": 14.68312917,
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 6.01736804,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.09354756,
                        "main_flow_out": 2.05735,
                        "secondary_flows_in": {"DIESEL-L": 0.00122321},
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
                        "OPEX-O": 0.00590844,
                        "WACC": 0.0487,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                        "mass": {
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.05735,
                        "main_flow_out": 2.05735,
                        "secondary_flows_in": {"EL": 0.041147},
                    },
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV": {"EL": 0.02},
                        "EFF": 1.0,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "WACC": 0.0487,
                        "process_code": "CH4-COMP#B",
                        "step": "PRE_PPL",
                    },
                    "process_code": "CH4-COMP#B",
                    "process_step": "PRE_PPL",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                        "mass": {
                            "co2_bound_in_product": 413.52735003,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                    },
                    "flows": {"main_flow_in": 2.05735, "main_flow_out": 2.05735},
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV-OT": {"NG-G": 3e-05},
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 1.0,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "LOSS-T": 2.04e-06,
                        "process_code": "CH4-P-S#B",
                        "step": "PPLS",
                    },
                    "process_code": "CH4-P-S#B",
                    "process_step": "PPLS",
                },
                {
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 38.68864459,
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 49.76296001,
                        },
                        "mass": {
                            "ch4_direct_co2e": 38.68864459,
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 49.76296001,
                        },
                    },
                    "flows": {"main_flow_in": 2.05735, "main_flow_out": 1.789},
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV-OT": {"NG-G": 3e-05},
                        "DIST": 5000.0,
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 0.86956522,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "LOSS": {"NG-G": 0.0102},
                        "LOSS-T": 2.04e-06,
                        "process_code": "CH4-P-L#B",
                        "step": "PPL",
                    },
                    "process_code": "CH4-P-L#B",
                    "process_step": "PPL",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                        "mass": {
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                    },
                    "flows": {"main_flow_in": 1.789, "main_flow_out": 1.789},
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV-OT": {"NG-G": 3e-05},
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 1.0,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "LOSS-T": 2.04e-06,
                        "process_code": "CH4-P-SR#B",
                        "step": "PPLX",
                    },
                    "process_code": "CH4-P-SR#B",
                    "process_step": "PPLX",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                        "mass": {
                            "co2_bound_in_product": 359.58900002,
                            "co2_bound_in_product_per_output": 201.00000001,
                        },
                    },
                    "flows": {"main_flow_in": 1.789, "main_flow_out": 1.789},
                    "parameter": {
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV-OT": {"NG-G": 3e-05},
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 1.0,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "LOSS-T": 2.04e-06,
                        "process_code": "CH4-P-LR#B",
                        "step": "PPLR",
                    },
                    "process_code": "CH4-P-LR#B",
                    "process_step": "PPLR",
                },
                {
                    "costs": {"CAPEX": 0.01234524, "OPEX": 0.00354703},
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
                        "main_flow_out": 1,
                        "secondary_flows_in": {"CO2-C": 0.08261781, "EL": 0.0115},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 1317.77881242,
                        "CBOUND": {"NG-G": 0.07279681},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"NG-G": 0.89},
                        "CO2CPT-S": {"NG-G": 0.25815306},
                        "CONV": {"EL": 0.0115},
                        "EFF": 0.55897149,
                        "EF_E": {"CO2-C": 1000.0, "EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 25.0,
                        "OPEX-F": 24.8292,
                        "WACC": 0.0423,
                        "process_code": "EFUELSYNC#B",
                        "step": "DERIV_I",
                    },
                    "process_code": "EFUELSYNC#B",
                    "process_step": "DERIV_I",
                },
                {
                    "costs": {"OPEX": 0.01524065},
                    "flows": {"main_flow_out": 0.08672787},
                    "is_in_import_segment": True,
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.17572953,
                        "WACC": 0.0423,
                        "process_code": "CO2-T+S#B",
                        "step": "SECONDARY:IMPORT:CO2-C",
                    },
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:IMPORT:CO2-C",
                },
                {
                    "costs": {"CAPEX": 0.00027945, "OPEX": 0.00012444},
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
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 2860.93056232,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 75.74556766,
                        "WACC": 0.0423,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:IMPORT:EL",
                    },
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:IMPORT:EL",
                },
                {
                    "costs": {"FLOW": 0.0008459},
                    "flows": {"main_flow_out": 0.02277628},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03713946}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
                {
                    "costs": {"FLOW": 6.228e-05},
                    "flows": {"main_flow_out": 0.00122321},
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.05091429}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:DIESEL-L",
                },
                {
                    "costs": {"FLOW": 0.00342178},
                    "flows": {"main_flow_out": 0.041147},
                    "parameter": {"SPECCOST": {"EL": 0.08316}},
                    "process_code": "EL",
                    "process_step": "MARKET:EL",
                },
                {"process_code": "NG-G", "process_step": "MARKET:NG-G"},
                {"process_code": "NG-G", "process_step": "MARKET:NG-G"},
                {"process_code": "NG-G", "process_step": "MARKET:NG-G"},
                {"process_code": "NG-G", "process_step": "MARKET:NG-G"},
            ],
            # marks=pytest.mark.skip,  # noqa
        ),
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
                    "costs": {"OPEX": 0.01070477},
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
                        "OPEX-O": 0.00590844,
                        "WACC": 0.0487,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "costs": {"CAPEX": 0.01318359, "OPEX": 0.00354703},
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
                        "CAPEX": 1317.77881242,
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
                        "OPEX-F": 24.8292,
                        "WACC": 0.0487,
                        "process_code": "EFUELSYNC#B",
                        "step": "DERIV",
                    },
                    "process_code": "EFUELSYNC#B",
                    "process_step": "DERIV",
                },
                {
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                        },
                        "mass": {
                            "co2_bound_in_product": 266.76000002,
                            "co2_bound_in_product_per_output": 266.76000002,
                        },
                    },
                    "flows": {"main_flow_in": 1.0, "main_flow_out": 1},
                    "parameter": {
                        "DIST": 12830.0,
                        "DST-S-D": 12830.0,
                        "DST-S-DP": 5000.0,
                        "EFF": 1.0,
                        "EF_M": {"BFUEL-L": 292.68},
                        "process_code": "SYN-SB#B",
                        "step": "SHP",
                    },
                    "process_code": "SYN-SB#B",
                    "process_step": "SHP",
                },
                {
                    "costs": {"OPEX": 0.00312174},
                    "flows": {"main_flow_out": 0.08672787},
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.03599464,
                        "WACC": 0.0487,
                        "process_code": "CO2-T+S#B",
                        "step": "SECONDARY:CO2-C",
                    },
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:CO2-C",
                },
                {
                    "costs": {"CAPEX": 0.00030123, "OPEX": 0.00012444},
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
                        "CAPEX": 2860.93056232,
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 75.74556766,
                        "WACC": 0.0487,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:EL",
                    },
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:EL",
                },
                {
                    "costs": {"FLOW": 5.485e-05},
                    "flows": {"main_flow_out": 0.00107721},
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.05091429}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:DIESEL-L",
                },
                {
                    "parameter": {"SPECCOST": {"BFUEL-L": 0.00331934}},
                    "process_code": "BFUEL-L",
                    "process_step": "MARKET:BFUEL-L",
                },
            ],
            # marks=pytest.mark.skip,  # noqa
        ),
        # =============================================================================
        # CASE 3
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
                    "costs": {"OPEX": 0.013259},
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 102.55099429,
                            "co2_bound_in_product": 693.5041164,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 63.99678779,
                        },
                        "mass": {
                            "ch4_direct_co2e": 102.55099429,
                            "co2_bound_in_product": 693.5041164,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 63.99678779,
                        },
                    },
                    "flows": {
                        "main_flow_in": 3.8215451,
                        "main_flow_out": 3.45026924,
                        "secondary_flows_in": {"DIESEL-L": 0.00207832},
                    },
                    "parameter": {
                        "CBOUND": {"NG-G": 0.0548514},
                        "CH4SHARE": {"NG-G": 0.89953333},
                        "CONV": {"DIESEL-L": 0.00060236},
                        "EFF": 0.90284666,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": {"NG-G": 0.01477525},
                        "OPEX-O": 0.00384289,
                        "WACC": 0.11949308,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    },
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "emission": {
                            "ch4_direct_co2e": 3.17791152,
                            "co2_bound_in_product": 594.39487854,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 98.76265908,
                        },
                        "mass": {
                            "ch4_direct_co2e": 3.17791152,
                            "co2_bound_in_product": 594.39487854,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 98.76265908,
                        },
                    },
                    "flows": {
                        "main_flow_in": 3.45026924,
                        "main_flow_out": 2.95718845,
                        "secondary_flows_in": {"EL": 0.00810722},
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
                        "WACC": 0.11949308,
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
                            "co2_direct": 2.1690815,
                        },
                        "mass": {
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 8.04454783,
                        },
                    },
                    "flows": {
                        "main_flow_in": 2.95718845,
                        "main_flow_out": 2.946397,
                        "secondary_flows_in": {"BFUEL-L": 0.02007471},
                    },
                    "parameter": {
                        "CONV": {"BFUEL-L": 0.00681331},
                        "CONV-OT": {"BFUEL-L": 2.15e-06, "NG-L": 1.12e-06},
                        "DIST": 3174.14,
                        "DST-S-D": 3174.14,
                        "DST-S-DP": 3000.0,
                        "EFF": 0.99635077,
                        "EF_E": {"NG-L": 201.0},
                        "EF_M": {"BFUEL-L": 292.68, "NG-L": 201.0},
                        "LOSS-T": 4e-08,
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
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.50496389,
                        },
                        "mass": {
                            "co2_bound_in_product": 592.22579704,
                            "co2_bound_in_product_per_output": 201.00000001,
                            "co2_direct": 0.50496389,
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
                        "WACC": 0.0423,
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                    "process_code": "CH4-RGAS#B",
                    "process_step": "POST_SHP",
                },
                {
                    "costs": {"CAPEX": 6.26e-06, "OPEX": 2.5e-06},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 148.05644926,
                            "co2_bound_in_product_per_output": 149.55196895,
                            "co2_captured": 239.8514478,
                            "co2_direct": 204.31789998,
                        },
                        "mass": {
                            "co2_bound_in_product": 148.05644926,
                            "co2_bound_in_product_per_output": 149.55196895,
                            "co2_captured": 239.8514478,
                            "co2_direct": 204.31789998,
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
                        "CAPEX": 0.58903758,
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
                        "OPEX-F": 0.01767113,
                        "WACC": 0.0423,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV_I",
                },
                {
                    "costs": {"CAPEX": 4.41e-06, "OPEX": 0.18420736},
                    "emissions": {
                        "emission": {
                            "co2_bound_in_product": 14.65778518,
                            "co2_bound_in_product_per_output": 14.65778518,
                            "co2_direct": 193.69866408,
                        },
                        "mass": {
                            "co2_bound_in_product": 14.65778518,
                            "co2_bound_in_product_per_output": 14.65778518,
                            "co2_direct": 193.69866408,
                        },
                    },
                    "flows": {
                        "main_flow_in": 0.99,
                        "main_flow_out": 1,
                        "secondary_flows_in": {"EL": 0.651, "NG-G": 0.3},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 0.4113896,
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "EFF": 1.01010101,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01234169,
                        "OPEX-O": 0.18420559,
                        "WACC": 0.0423,
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "costs": {"OPEX": 0.11277353},
                    "flows": {"main_flow_out": 0.6417449},
                    "is_in_import_segment": True,
                    "parameter": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1000.0},
                        "EF_M": {"CO2-C": 1000.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "OPEX-O": 0.17572953,
                        "WACC": 0.0423,
                        "process_code": "CO2-T+S#B",
                        "step": "SECONDARY:IMPORT:CO2-C",
                    },
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY:IMPORT:CO2-C",
                },
                {
                    "costs": {"CAPEX": 0.02732531, "OPEX": 0.01216803},
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
                        "CAPEX": 2860.93056232,
                        "CH4SHARE": {"NG-G": 0.92080641},
                        "CO2CPT-R": {"NG-G": 0.89777778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.50491129,
                        "EF_E": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "EF_M": {"CO2-C": 1000.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 75.74556766,
                        "WACC": 0.0423,
                        "process_code": "CCGT-CC#B",
                        "step": "SECONDARY:IMPORT:EL",
                    },
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:IMPORT:EL",
                },
                {
                    "costs": {"FLOW": 0.08271448},
                    "flows": {"main_flow_out": 2.22713235},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03713946}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
                {
                    "costs": {"FLOW": 0.00010582},
                    "flows": {"main_flow_out": 0.00207832},
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.05091429}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:DIESEL-L",
                },
                {
                    "costs": {"FLOW": 0.0006742},
                    "flows": {"main_flow_out": 0.00810722},
                    "parameter": {"SPECCOST": {"EL": 0.08316}},
                    "process_code": "EL",
                    "process_step": "MARKET:EL",
                },
                {
                    "costs": {"FLOW": 6.663e-05},
                    "flows": {"main_flow_out": 0.02007471},
                    "parameter": {"SPECCOST": {"BFUEL-L": 0.00331934}},
                    "process_code": "BFUEL-L",
                    "process_step": "MARKET:BFUEL-L",
                },
                {"process_code": "NG-L", "process_step": "MARKET:NG-L"},
                {
                    "costs": {"FLOW": 9.301e-05},
                    "flows": {"main_flow_out": 0.00250444},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03713946}},
                    "process_code": "NG-G",
                    "process_step": "MARKET:IMPORT:NG-G",
                },
                {
                    "costs": {"FLOW": 3e-07},
                    "flows": {"main_flow_out": 5.89e-06},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"DIESEL-L": 0.05091429}},
                    "process_code": "DIESEL-L",
                    "process_step": "MARKET:IMPORT:DIESEL-L",
                },
                {
                    "is_in_import_segment": True,
                    "process_code": "CH4-G",
                    "process_step": "MARKET:IMPORT:CH4-G",
                },
                {
                    "costs": {"FLOW": 0.36429995},
                    "flows": {"main_flow_out": 1.36},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"IOP-S": 0.26786761}},
                    "process_code": "IOP-S",
                    "process_step": "MARKET:IMPORT:IOP-S",
                },
                {
                    "costs": {"FLOW": 0.01114184},
                    "flows": {"main_flow_out": 0.3},
                    "is_in_import_segment": True,
                    "parameter": {"SPECCOST": {"NG-G": 0.03713946}},
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
                    "costs": {"CAPEX": 0.00836554, "OPEX": 0.00465067},
                    "emissions": {
                        "mass": {
                            "co2_bound_in_product": 248.4875171,
                            "co2_bound_in_product_per_output": 1000.00000007,
                        }
                    },
                    "flows": {
                        "main_flow_in": 0.24848752,
                        "main_flow_out": 0.24848752,
                        "secondary_flows_in": {"EL": 0.05590969, "HEAT": 0.37273128},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 0.46789733,
                        "CBOUND": {"CO2-DAC": 0.27289252},
                        "CONV": {"EL": 0.225, "HEAT": 1.5},
                        "EFF": 1.0,
                        "EF_E": {"EL": 288.0, "HEAT": 201.0},
                        "EF_M": {"CO2-DAC": 1000.0, "EL": 288.0, "HEAT": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 25.0,
                        "OPEX-F": 0.01871589,
                        "WACC": 0.0514,
                        "process_code": "DAC#B",
                        "step": "SECONDARY:IMPORT:CO2-G",
                    },
                    "process_code": "DAC#B",
                    "process_step": "SECONDARY:IMPORT:CO2-G",
                },
                "DERIV_I": {
                    "costs": {"CAPEX": 0.00878339, "OPEX": 0.00398682},
                    "emissions": {
                        "mass": {
                            "co2_bound_in_product": 248.49429268,
                            "co2_bound_in_product_per_output": 248.49429268,
                        }
                    },
                    "flows": {
                        "main_flow_in": 1.16206724,
                        "main_flow_out": 1,
                        "secondary_flows_in": {"CO2-G": 0.24848752, "EL": 0.05368791},
                    },
                    "is_in_import_segment": True,
                    "parameter": {
                        "CAPEX": 930.25740791,
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
                        "OPEX-F": 27.90772224,
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

    for chain_name, chain in df_chains.iterrows():
        transport: TransportType = "Pipeline" if chain["can_pipeline"] else "Ship"
        ship_own_fuel: bool = (
            transport == "Ship" and chain["flow_out"] in flows_own_fuel
        )
        # Create different routes so we can test all 4 pipeline types
        # only for Norway/Spain + Algeria/Spain can we test all!
        if transport == "Pipeline" and chain["flow_out"] in flows_own_fuel:
            region = "Algeria"
        else:
            region = "Norway"
        country = "Spain"

        api.calculate(
            scenario="2030 (medium)",
            secproc_co2="Direct Air Capture (blue)",
            secproc_water=None,
            chain=chain_name,  # type: ignore
            res_gen=None,
            region=region,
            country=country,
            transport=transport,
            ship_own_fuel=ship_own_fuel,
            output_unit="USD/t",
            optimize_flh=False,
            tool_version_color="blue",
        )


def test_emissions_issue_775():
    """Create one instance of each blue chain andcheck expected results (totals)."""
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)

    actual_results = []

    for secproc_co2 in SecProcCO2Values:
        if secproc_co2 == "Direct Air Capture":
            continue  # only blue
        for demand_supply in ["demand", "supply"]:
            chain = f"CH3OH-L__ATR_91%_CH3OHSYN__prod_in_{demand_supply}"
            result = api.calculate(
                scenario="2040 (medium)",
                secproc_co2=secproc_co2,
                secproc_water="Sea Water desalination",
                chain=chain,  # type: ignore
                res_gen=None,
                region="Algeria",
                country="Germany",
                transport="Ship",
                ship_own_fuel=False,
                output_unit="USD/t",
                optimize_flh=False,
                tool_version_color="blue",
            )

            # get all co2_bound_in_product
            for mass_emission, df_e in [
                ("emission", result.emissions_t_co2e),
                ("mass", result.emission_mass_t_co2e),
            ]:
                actual_result = {
                    "demand_supply": demand_supply,
                    "secproc_co2": secproc_co2,
                    "mass_emission": mass_emission,
                    "co2_bound_in_product": [],
                }
                actual_results.append(actual_result)

                for process_data in result._internal_process_data:
                    try:
                        actual_result["co2_bound_in_product"].append(
                            {
                                "process": process_data["process_code"],
                                "value": process_data["emissions"][mass_emission][
                                    "co2_bound_in_product"
                                ],
                            }
                        )

                    except KeyError:
                        pass

                # final bound in product
                try:
                    actual_result["co2_bound_in_product"].append(
                        {
                            "process": "Bound in product",
                            "value": df_e.loc[
                                df_e["process_type"] == "Bound in product",
                                "values",
                            ].iloc[0],
                        }
                    )
                except IndexError:
                    pass

    expected_reults = [
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDF#B", "value": 248.4875171},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "demand",
            "mass_emission": "emission",
            "secproc_co2": "CO2 from fossil source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDF#B", "value": 248.4875171},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "demand",
            "mass_emission": "mass",
            "secproc_co2": "CO2 from fossil source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 365.24379779},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.68372319},
                {"process": "CH3OH-SB#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDF#B", "value": 248.67694245},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "supply",
            "mass_emission": "emission",
            "secproc_co2": "CO2 from fossil source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 365.24379779},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.68372319},
                {"process": "CH3OH-SB#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDF#B", "value": 248.67694245},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "supply",
            "mass_emission": "mass",
            "secproc_co2": "CO2 from fossil source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B"},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDS#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
            ],
            "demand_supply": "demand",
            "mass_emission": "emission",
            "secproc_co2": "CO2 from sustainable source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDS#B", "value": 248.4875171},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "demand",
            "mass_emission": "mass",
            "secproc_co2": "CO2 from sustainable source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 365.24379779},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B"},
                {"process": "CH3OH-SB#B"},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDS#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
            ],
            "demand_supply": "supply",
            "mass_emission": "emission",
            "secproc_co2": "CO2 from sustainable source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 365.24379779},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.68372319},
                {"process": "CH3OH-SB#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CO2-INDS#B", "value": 248.67694245},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "supply",
            "mass_emission": "mass",
            "secproc_co2": "CO2 from sustainable source",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B"},
                {"process": "CO2-T+S#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "DAC#B"},
            ],
            "demand_supply": "demand",
            "mass_emission": "emission",
            "secproc_co2": "Direct Air Capture (blue)",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 351.31682574},
                {"process": "CH4-LIQ#B", "value": 301.10985217},
                {"process": "CH4-SB#B", "value": 300.01103414},
                {"process": "CH4-RGAS#B", "value": 300.01103414},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "DAC#B", "value": 248.4875171},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "demand",
            "mass_emission": "mass",
            "secproc_co2": "Direct Air Capture (blue)",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 427.35594503},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B"},
                {"process": "CH3OH-SB#B"},
                {"process": "CO2-T+S#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "DAC#B"},
            ],
            "demand_supply": "supply",
            "mass_emission": "emission",
            "secproc_co2": "Direct Air Capture (blue)",
        },
        {
            "co2_bound_in_product": [
                {"process": "NG-PROD#B", "value": 427.35594503},
                {"process": "ATR_91%#B"},
                {"process": "CH3OHSYN#B", "value": 248.68372319},
                {"process": "CH3OH-SB#B", "value": 248.49429268},
                {"process": "CO2-T+S#B"},
                {"process": "CCGT-CC#B"},
                {"process": "HEATPUMP#B"},
                {"process": "DAC#B", "value": 248.67694245},
                {"process": "Bound in product", "value": 1.37362123},
            ],
            "demand_supply": "supply",
            "mass_emission": "mass",
            "secproc_co2": "Direct Air Capture (blue)",
        },
    ]
    assert_deep_equal_approx(expected_reults, actual_results)
