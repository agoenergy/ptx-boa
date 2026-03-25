"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from tests.test_api import ptxdata_dir_static


def _sort_nested(xs):
    if isinstance(xs, list):
        return [_sort_nested(x) for x in xs]
    elif isinstance(xs, dict):
        return {x: _sort_nested(xs[x]) for x in sorted(xs.keys())}
    else:
        return xs


def _round_nested(xs, ndigis: int = 6, drop_null_from_dict: bool = True):
    if isinstance(xs, list):
        result = [
            _round_nested(x, ndigis, drop_null_from_dict=drop_null_from_dict)
            for x in xs
        ]
        if drop_null_from_dict:
            result = [x for x in result if x]
        return result
    elif isinstance(xs, dict):
        result = {
            x: _round_nested(y, ndigis, drop_null_from_dict=drop_null_from_dict)
            for x, y in xs.items()
        }
        if drop_null_from_dict:
            # drop enire dict containing "values": 0
            if "values" in result and not result["values"]:
                result = {}
            else:
                result = {x: y for x, y in result.items() if y}
        return result
    elif isinstance(xs, float):
        return round(xs, ndigis)
    else:
        return xs


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
                dim = DataHandler.dimensions[dimname]  # type:ignore
                try:
                    value = dim.loc[value, basename + "_name"]
                except Exception:
                    raise KeyError(
                        f"{colname}={value} not in {dimname}: "
                        f"{sorted(dim.index)}, {sorted(dim.columns)}"
                    )
                user_data.loc[idx, colname] = value  # type:ignore


# recursively use pytest.approx
def _rec_approx(x):
    if isinstance(x, dict):
        return {k: _rec_approx(v) for k, v in x.items()}
    elif isinstance(x, list):
        return [_rec_approx(v) for v in x]
    elif isinstance(x, (int, float)):
        return pytest.approx(x)
    else:
        return x


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
                "use_ship": True,
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
            # FIXME: all flows are (in green tool) expected to have CALOR
            # but doesit make sense for Steel?
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
                "flow_code": "STL-S",
                "parameter_code": "CALOR",
                "value": 0,
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

    data_handler = DataHandler(
        data_dir=ptxdata_dir_static,
        scenario=scenario,
        user_data=user_data,
        tool_version_color="blue",
    )
    calculation_data_ = data_handler.get_calculation_data(**kwargs, optimize_flh=False)
    ptxcalc_results = PtxCalc.calculate(calculation_data_)  # type:ignore

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
    res_emission_mass = api_result.emission_mass[  # type:ignore
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")

    # round and sort for easier comparison
    values = _sort_nested(_round_nested(ptxcalc_results.results_flows_chain))
    # round and sort for easier comparison
    calculation_data = _sort_nested(_round_nested(calculation_data_))
    res_emission_mass = _sort_nested(_round_nested(res_emission_mass))

    # print so we can copy/paste new results into test
    print("calculation_data_exp = ", calculation_data)
    print("values_exp = ", values)
    print("res_emission_mass_exp = ", res_emission_mass)

    calculation_data_exp = {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "main_export_process_chain": [
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
            }
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
        "parameter": {
            "SPECCOST": {
                "CO2-G": 0.044519,
                "EL": 0.08078,
                "H2O-L": 0.001374,
                "HEAT": 0.0577,
                "N2-G": 0.01154,
            }
        },
        "parameter_i": {
            "SPECCOST": {
                "CO2-G": 0.044519,
                "EL": 0.08078,
                "H2O-L": 0.001374,
                "HEAT": 0.0577,
                "N2-G": 0.01154,
            }
        },
        "transport_process_chain": [
            {"DIST": 999.0, "EFF": 1.0, "process_code": "DRI-SB#B", "step": "SHP"}
        ],
    }
    values_exp = [
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
                "co2_indirect_scope2_e": 189.780347,
                "co2_indirect_scope2_m": 189.780347,
                "co2e_total_direct_e": 478.690291,
                "co2e_total_direct_m": 478.690291,
            },
            "flows": {"CO2-C": 0.239851, "EL": 0.47209, "IOP-S": 1.36},
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
                "ch4_direct_co2e_e": 0.372488,
                "ch4_direct_co2e_m": 0.372488,
                "ch4_direct_e": 0.0125,
                "ch4_direct_m": 0.0125,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_direct_e": 148.05785,
                "co2_direct_m": 148.86185,
                "co2_in_flows_m": 0.804,
                "co2_indirect_scope2_e": 195.3,
                "co2_indirect_scope2_m": 195.3,
                "co2e_total_direct_e": 148.430338,
                "co2e_total_direct_m": 149.234338,
            },
            "flows": {"EL": 0.651, "NG-G": 0.0042},
            "main_input": 0.99,
            "main_output": 1.0,
            "process_code": "EAF#B",
            "process_step": "DERIV_I",
        },
    ]
    res_emission_mass_exp = [
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "EAF#B",
            "values": 372.488202,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "EAF#B",
            "values": 148861.84985,
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
            "values": 274374.20694,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "NG-DRI-C#B",
            "values": 204316.083746,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "NG-DRI-C#B",
            "values": 189780.346718,
        },
    ]

    assert _rec_approx(calculation_data) == calculation_data_exp
    assert _rec_approx(values) == values_exp
    assert _rec_approx(res_emission_mass) == res_emission_mass_exp


@pytest.mark.parametrize(
    "api_kwargs,calculation_data_exp,values_exp,res_emission_mass_exp,res_costs_exp",
    [
        # =============================================================================
        # CASE 1
        # ==============================================================================
        [
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
                "secproc_el": "Combined Cycle Gas Turbine with CCS (blue)",
                "secproc_heat": "Large scale Heatpump (blue)",
            },
            {
                "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
                "main_export_process_chain": [
                    {
                        "CBOUND": {"NG-G": 0.054851},
                        "CH4SHARE": {"NG-G": 0.909},
                        "CONV": {"DIESEL-L": 0.000595, "EL": 0.001153},
                        "EFF": 0.98271,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": 0.00378,
                        "OPEX-O": 0.004863,
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
                        "EFF": 0.336004,
                        "EF_E": {"CH4-G": 201.0, "NG-G": 201.0},
                        "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.017756,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV",
                    },
                ],
                "main_import_process_chain": [
                    {
                        "CAPEX": 0.417344,
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CH4SHARE": {"NG-G": 0.920806},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "EFF": 1.010101,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01252,
                        "OPEX-O": 0.183679,
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    }
                ],
                "parameter": {
                    "CALOR": 1,
                    "SPECCOST": {
                        "CO2-G": 0.044519,
                        "DIESEL-L": 0.042857,
                        "H2O-L": 0.001374,
                        "HEAT": 0.0577,
                        "IOP-S": 0.267076,
                        "N2-G": 0.01154,
                    },
                    "WACC": 0.0487,
                },
                "parameter_i": {
                    "CALOR": 1,
                    "SPECCOST": {
                        "CO2-G": 0.044519,
                        "DIESEL-L": 0.042857,
                        "H2O-L": 0.001374,
                        "HEAT": 0.04,
                        "IOP-S": 0.267076,
                        "N2-G": 0.01154,
                    },
                    "WACC": 0.0423,
                },
                "secondary_process": {
                    "EL": {
                        "CAPEX": 2408.190709,
                        "CH4SHARE": {"NG-G": 0.909},
                        "CO2CPT-R": {"NG-G": 0.897778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.504911,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.758895,
                        "process_code": "CCGT-CC#B",
                    }
                },
                "secondary_process_i": {
                    "EL": {
                        "CAPEX": 2408.190709,
                        "CH4SHARE": {"NG-G": 0.920806},
                        "CO2CPT-R": {"NG-G": 0.897778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.504911,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.758895,
                        "process_code": "CCGT-CC#B",
                    }
                },
                "transport_process_chain": [
                    {
                        "DIST": 12830.0,
                        "EFF": 1.0,
                        "process_code": "DRI-SB#B",
                        "step": "SHP",
                    }
                ],
            },
            [
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 21.028181,
                        "ch4_direct_co2e_m": 21.028181,
                        "ch4_direct_e": 0.705644,
                        "ch4_direct_m": 0.705644,
                        "co2_bound_in_product_e": 592.225797,
                        "co2_bound_in_product_m": 592.225797,
                        "co2_direct_e": 8.617666,
                        "co2_direct_m": 8.617666,
                        "co2_in_flows_e": 600.843463,
                        "co2_in_flows_m": 600.843463,
                        "co2e_total_direct_e": 29.645847,
                        "co2e_total_direct_m": 29.645847,
                    },
                    "flows": {"DIESEL-L": 0.001752, "EL": 0.003397},
                    "main_input": 2.998237,
                    "main_output": 2.946397,
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.056449,
                        "co2_bound_in_product_last_proc_e": 592.225797,
                        "co2_bound_in_product_last_proc_m": 592.225797,
                        "co2_bound_in_product_m": 148.056449,
                        "co2_captured_e": 239.851448,
                        "co2_captured_m": 239.851448,
                        "co2_direct_e": 796.543697,
                        "co2_direct_m": 796.543697,
                        "co2_in_flows_e": 592.225797,
                        "co2_in_flows_m": 592.225797,
                        "co2e_total_direct_e": 796.543697,
                        "co2e_total_direct_m": 796.543697,
                    },
                    "flows": {"CO2-C": 0.239851, "EL": 0.47209, "IOP-S": 1.36},
                    "main_input": 2.946397,
                    "main_output": 0.99,
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.056449,
                        "co2_bound_in_product_last_proc_e": 148.056449,
                        "co2_bound_in_product_last_proc_m": 148.056449,
                        "co2_bound_in_product_m": 148.056449,
                    },
                    "main_input": 0.99,
                    "main_output": 0.99,
                    "process_code": "DRI-SB#B",
                    "process_step": "SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 14.657785,
                        "co2_bound_in_product_last_proc_e": 148.056449,
                        "co2_bound_in_product_last_proc_m": 148.056449,
                        "co2_bound_in_product_m": 14.657785,
                        "co2_direct_e": 193.698664,
                        "co2_direct_m": 193.698664,
                        "co2_in_flows_e": 60.3,
                        "co2_in_flows_m": 60.3,
                        "co2_indirect_scope2_e": 65.1,
                        "co2_indirect_scope2_m": 65.1,
                        "co2e_total_direct_e": 193.698664,
                        "co2e_total_direct_m": 193.698664,
                    },
                    "flows": {"EL": 0.651, "NG-G": 0.3},
                    "main_input": 0.99,
                    "main_output": 1.0,
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "main_input": 0.475487,
                    "main_output": 0.475487,
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:Electricity",
                },
                {
                    "main_input": 0.651,
                    "main_output": 0.651,
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY-IMPORT:Electricity",
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
                    "values": 193698.66408,
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
                    "process_subtype": "NG-DRI-C#B",
                    "values": 796543.696995,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "NG-PROD#B",
                    "values": 21028.18078,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-PROD#B",
                    "values": 8617.665995,
                },
            ],
            [
                {
                    "process_subtype": "CCGT-CC#B",
                    "process_type": "Electricity",
                    "values": 103704.27343,
                },
                {
                    "process_subtype": "CCGT-CC#B (import)",
                    "process_type": "Electricity",
                    "values": 134717.907566,
                },
                {
                    "process_subtype": "DRI-SB#B",
                    "process_type": "Transportation (Ship)",
                    "values": 4.782676,
                },
                {
                    "process_subtype": "EAF#B",
                    "process_type": "Derivative production",
                    "values": 183.684956,
                },
                {
                    "process_subtype": "NG-DRI-C#B",
                    "process_type": "Derivative production",
                    "values": 363.232485,
                },
                {
                    "process_subtype": "NG-PROD#B",
                    "process_type": "Natural gas production",
                    "values": 14.402131,
                },
            ],
        ],
        # =============================================================================
        # CASE 2
        # ==============================================================================
        [
            {
                "scenario": "2040 (medium)",
                "region": "Algeria",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_demand",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
                "secproc_el": "Combined Cycle Gas Turbine with CCS (blue)",
                "secproc_heat": "Large scale Heatpump (blue)",
            },
            {
                "context": {"source_region_code": "DZA", "target_country_code": "DEU"},
                "main_export_process_chain": [
                    {
                        "CBOUND": {"NG-G": 0.054851},
                        "CH4SHARE": {"NG-G": 0.899533},
                        "CONV": {"DIESEL-L": 0.000602, "EL": 0.000307},
                        "EFF": 0.903626,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "LOSS": 0.0139,
                        "OPEX-O": 0.003163,
                        "process_code": "NG-PROD#B",
                        "step": "NG_PROD",
                    }
                ],
                "main_import_process_chain": [
                    {
                        "CAPEX": 0.591876,
                        "CBOUND": {"NG-G": 0.040812},
                        "CH4SHARE": {"NG-G": 0.920806},
                        "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                        "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                        "CONV": {"CO2-C": 1, "EL": 0.476859, "IOP-S": 1.373737},
                        "EFF": 0.336004,
                        "EF_E": {"CH4-G": 201.0, "EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"CH4-G": 201.0, "EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.017756,
                        "process_code": "NG-DRI-C#B",
                        "step": "DERIV_I",
                    },
                    {
                        "CAPEX": 0.417344,
                        "CBOUND": {"B-DRI-S": 0.004},
                        "CH4SHARE": {"NG-G": 0.920806},
                        "CONV": {"EL": 0.651, "NG-G": 0.3},
                        "EFF": 1.010101,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20.0,
                        "OPEX-F": 0.01252,
                        "OPEX-O": 0.183679,
                        "process_code": "EAF#B",
                        "step": "DERIV_I2",
                    },
                ],
                "parameter": {
                    "CALOR": 1,
                    "SPECCOST": {
                        "CO2-G": 0.044519,
                        "DIESEL-L": 0.042857,
                        "EL": 0.08078,
                        "H2O-L": 0.001374,
                        "HEAT": 0.0577,
                        "IOP-S": 0.267076,
                        "N2-G": 0.01154,
                    },
                    "WACC": 0.145548,
                },
                "parameter_i": {
                    "CALOR": 1,
                    "SPECCOST": {
                        "CO2-G": 0.044519,
                        "DIESEL-L": 0.042857,
                        "EL": 0.1,
                        "H2O-L": 0.001374,
                        "HEAT": 0.04,
                        "IOP-S": 0.267076,
                        "N2-G": 0.01154,
                    },
                    "WACC": 0.0423,
                },
                "secondary_process": {
                    "EL": {
                        "CAPEX": 2408.190709,
                        "CH4SHARE": {"NG-G": 0.899533},
                        "CO2CPT-R": {"NG-G": 0.897778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.504911,
                        "EF_E": {"NG-G": 201.0},
                        "EF_M": {"NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.758895,
                        "process_code": "CCGT-CC#B",
                    }
                },
                "secondary_process_i": {
                    "CO2-C": {
                        "EFF": 0.95,
                        "EF_E": {"CO2-C": 1.0, "EL": 100.0},
                        "EF_M": {"CO2-C": 1.0, "EL": 100.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "process_code": "CO2-T+S#B",
                    },
                    "EL": {
                        "CAPEX": 2408.190709,
                        "CH4SHARE": {"NG-G": 0.920806},
                        "CO2CPT-R": {"NG-G": 0.897778},
                        "CO2CPT-S": {"NG-G": 1.0},
                        "EFF": 0.504911,
                        "EF_E": {"EL": 100.0, "NG-G": 201.0},
                        "EF_M": {"EL": 100.0, "NG-G": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "OPEX-F": 63.758895,
                        "process_code": "CCGT-CC#B",
                    },
                },
                "transport_process_chain": [
                    {
                        "CAPEX": 408.107082,
                        "CH4SHARE": {"NG-G": 0.899533},
                        "CONV": {"EL": 0.002742},
                        "EFF": 0.857089,
                        "EF_E": {"NG-G": 201.0, "NG-L": 201.0},
                        "EF_M": {"NG-G": 201.0, "NG-L": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 30.0,
                        "LOSS": 0.0005,
                        "OPEX-F": 8.162142,
                        "process_code": "CH4-LIQ#B",
                        "step": "PRE_SHP",
                    },
                    {
                        "DIST": 3174.14,
                        "EFF": 1.0,
                        "process_code": "CH4-SB#B",
                        "step": "SHP",
                    },
                    {
                        "CH4SHARE": {"NG-G": 0.899533},
                        "CONV": {"DIESEL-L": 2e-06, "EL": 0.00048, "NG-G": 0.00085},
                        "EFF": 1,
                        "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0, "NG-L": 201.0},
                        "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0, "NG-L": 201.0},
                        "FLH": 7000,
                        "LIFETIME": 20,
                        "process_code": "CH4-RGAS#B",
                        "step": "POST_SHP",
                    },
                ],
            },
            [
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 96.124057,
                        "ch4_direct_co2e_m": 96.124057,
                        "ch4_direct_e": 3.225639,
                        "ch4_direct_m": 3.225639,
                        "co2_bound_in_product_e": 690.973363,
                        "co2_bound_in_product_m": 690.973363,
                        "co2_direct_e": 63.763249,
                        "co2_direct_m": 63.763249,
                        "co2_in_flows_e": 754.736612,
                        "co2_in_flows_m": 754.736612,
                        "co2e_total_direct_e": 159.887306,
                        "co2e_total_direct_m": 159.887306,
                    },
                    "flows": {"DIESEL-L": 0.002071, "EL": 0.001055},
                    "main_input": 3.804315,
                    "main_output": 3.437678,
                    "process_code": "NG-PROD#B",
                    "process_step": "NG_PROD",
                },
                {
                    "emissions": {
                        "ch4_direct_co2e_e": 3.166315,
                        "ch4_direct_co2e_m": 3.166315,
                        "ch4_direct_e": 0.106252,
                        "ch4_direct_m": 0.106252,
                        "co2_bound_in_product_e": 592.225797,
                        "co2_bound_in_product_last_proc_e": 690.973363,
                        "co2_bound_in_product_last_proc_m": 690.973363,
                        "co2_bound_in_product_m": 592.225797,
                        "co2_direct_e": 789.375615,
                        "co2_direct_m": 789.375615,
                        "co2_in_flows_e": 690.628049,
                        "co2_in_flows_m": 690.628049,
                        "co2e_total_direct_e": 792.541929,
                        "co2e_total_direct_m": 792.541929,
                    },
                    "flows": {"EL": 0.008078},
                    "main_input": 3.437678,
                    "main_output": 2.946397,
                    "process_code": "CH4-LIQ#B",
                    "process_step": "PRE_SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 592.225797,
                        "co2_bound_in_product_last_proc_e": 592.225797,
                        "co2_bound_in_product_last_proc_m": 592.225797,
                        "co2_bound_in_product_m": 592.225797,
                    },
                    "main_input": 2.946397,
                    "main_output": 2.946397,
                    "process_code": "CH4-SB#B",
                    "process_step": "SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 592.225797,
                        "co2_bound_in_product_last_proc_e": 592.225797,
                        "co2_bound_in_product_last_proc_m": 592.225797,
                        "co2_bound_in_product_m": 592.225797,
                        "co2_direct_e": 592.730761,
                        "co2_direct_m": 592.730761,
                        "co2_in_flows_e": 592.730761,
                        "co2_in_flows_m": 592.730761,
                        "co2e_total_direct_e": 592.730761,
                        "co2e_total_direct_m": 592.730761,
                    },
                    "flows": {"DIESEL-L": 6e-06, "EL": 0.001414, "NG-G": 0.002504},
                    "main_input": 2.946397,
                    "main_output": 2.946397,
                    "process_code": "CH4-RGAS#B",
                    "process_step": "POST_SHP",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 148.056449,
                        "co2_bound_in_product_last_proc_e": 592.225797,
                        "co2_bound_in_product_last_proc_m": 592.225797,
                        "co2_bound_in_product_m": 148.056449,
                        "co2_captured_e": 239.851448,
                        "co2_captured_m": 239.851448,
                        "co2_direct_e": 796.543697,
                        "co2_direct_m": 796.543697,
                        "co2_in_flows_e": 592.225797,
                        "co2_in_flows_m": 592.225797,
                        "co2_indirect_scope2_e": 47.209,
                        "co2_indirect_scope2_m": 47.209,
                        "co2e_total_direct_e": 796.543697,
                        "co2e_total_direct_m": 796.543697,
                    },
                    "flows": {"CO2-C": 0.239851, "EL": 0.47209, "IOP-S": 1.36},
                    "main_input": 2.946397,
                    "main_output": 0.99,
                    "process_code": "NG-DRI-C#B",
                    "process_step": "DERIV_I",
                },
                {
                    "emissions": {
                        "co2_bound_in_product_e": 14.657785,
                        "co2_bound_in_product_last_proc_e": 148.056449,
                        "co2_bound_in_product_last_proc_m": 148.056449,
                        "co2_bound_in_product_m": 14.657785,
                        "co2_direct_e": 193.698664,
                        "co2_direct_m": 193.698664,
                        "co2_in_flows_e": 60.3,
                        "co2_in_flows_m": 60.3,
                        "co2_indirect_scope2_e": 65.1,
                        "co2_indirect_scope2_m": 65.1,
                        "co2e_total_direct_e": 193.698664,
                        "co2e_total_direct_m": 193.698664,
                    },
                    "flows": {"EL": 0.651, "NG-G": 0.3},
                    "main_input": 0.99,
                    "main_output": 1.0,
                    "process_code": "EAF#B",
                    "process_step": "DERIV_I2",
                },
                {
                    "main_input": 0.010547,
                    "main_output": 0.010547,
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY:Electricity",
                },
                {
                    "main_input": 1.12309,
                    "main_output": 1.12309,
                    "process_code": "CCGT-CC#B",
                    "process_step": "SECONDARY-IMPORT:Electricity",
                },
                {
                    "main_input": 0.239851,
                    "main_output": 0.239851,
                    "process_code": "CO2-T+S#B",
                    "process_step": "SECONDARY-IMPORT:Captured Carbon",
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
                    "values": 193698.66408,
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
                    "process_subtype": "NG-DRI-C#B",
                    "values": 796543.696995,
                },
                {
                    "emission_type": "indirect",
                    "gas_type": "CO2",
                    "process_subtype": "NG-DRI-C#B",
                    "values": 47209.0,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "NG-PROD#B",
                    "values": 96124.056584,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "NG-PROD#B",
                    "values": 63763.249017,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "CH4-LIQ#B",
                    "values": 3166.314605,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CH4-LIQ#B",
                    "values": 789375.614575,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CH4",
                    "process_subtype": "CH4-RGAS#B",
                    "values": 0.000185,
                },
                {
                    "emission_type": "direct",
                    "gas_type": "CO2",
                    "process_subtype": "CH4-RGAS#B",
                    "values": 592730.760889,
                },
            ],
            [
                {
                    "process_subtype": "CCGT-CC#B",
                    "process_type": "Electricity",
                    "values": 4433.156143,
                },
                {
                    "process_subtype": "CCGT-CC#B (import)",
                    "process_type": "Electricity",
                    "values": 232412.188645,
                },
                {
                    "process_subtype": "CH4-LIQ#B",
                    "process_type": "Transportation (Ship)",
                    "values": 28.869076,
                },
                {
                    "process_subtype": "CH4-RGAS#B",
                    "process_type": "Transportation (Ship)",
                    "values": 0.000253,
                },
                {
                    "process_subtype": "CH4-SB#B",
                    "process_type": "Transportation (Ship)",
                    "values": 2.376934,
                },
                {
                    "process_subtype": "EAF#B",
                    "process_type": "Derivative production",
                    "values": 183.684956,
                },
                {
                    "process_subtype": "NG-DRI-C#B",
                    "process_type": "Derivative production",
                    "values": 363.232128,
                },
                {
                    "process_subtype": "NG-PROD#B",
                    "process_type": "Natural gas production",
                    "values": 10.960904,
                },
            ],
        ],
    ],
)
def test_new_blue_chain_real_data(
    api_kwargs, calculation_data_exp, values_exp, res_emission_mass_exp, res_costs_exp
):
    """Data test for blue iron chain using current data."""
    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    api_result = api.calculate(  # noqa
        **api_kwargs,
        tool_version_color="blue",
        optimize_flh=False,
    )

    calculation_data = _sort_nested(_round_nested(api_result.todo_data))
    values = _sort_nested(_round_nested(api_result.todo_results_flows))

    res_emission_mass = api_result.emission_mass[  # type:ignore
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")
    # round and sort for easier comparison
    res_emission_mass = _sort_nested(_round_nested(res_emission_mass))

    res_costs = (
        api_result.costs[  # type:ignore
            ["process_subtype", "process_type", "values"]
        ]
        .groupby(["process_subtype", "process_type"])
        .sum()
        .reset_index()
        .to_dict(orient="records")
    )
    # round and sort for easier comparison
    res_costs = _sort_nested(_round_nested(res_costs))

    # print so we can copy/paste new results into test
    print((calculation_data, values, res_emission_mass, res_costs))

    assert _rec_approx(calculation_data) == _sort_nested(
        _round_nested(calculation_data_exp)
    )
    assert _rec_approx(values) == _sort_nested(_round_nested(values_exp))
    assert _rec_approx(res_emission_mass) == _sort_nested(
        _round_nested(res_emission_mass_exp)
    )
    assert _rec_approx(res_costs) == _sort_nested(_round_nested(res_costs_exp))
