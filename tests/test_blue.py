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


def _round_nested(xs, ndigis: int = 6):
    if isinstance(xs, list):
        return [_round_nested(x, ndigis) for x in xs]
    elif isinstance(xs, dict):
        return {x: _round_nested(y, ndigis) for x, y in xs.items()}
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
                "parameter_code": "CO2BOUND",
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
                "parameter_code": "CO2BOUND",
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
    calculation_data = data_handler.get_calculation_data(**kwargs, optimize_flh=False)
    # round and sort for easier comparison
    calculation_data = _sort_nested(_round_nested(calculation_data))

    values, _df_result_cost, _df_result_emissions, _df_result_emissions_mass = (
        PtxCalc.calculate(calculation_data)
    )  # noqa
    # round and sort for easier comparison
    values = _sort_nested(_round_nested(values))

    # test api output
    api = PtxboaAPI(data_dir=ptxdata_dir_static)
    api_result = api.calculate(  # noqa
        scenario=scenario,
        **api_kwargs,
        user_data=user_data,
        tool_version_color="blue",
        optimize_flh=False,
    )
    res_emission_mass = api_result.emission_mass[
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")
    res_emission_mass = _sort_nested(_round_nested(res_emission_mass))

    # print so we can copy/paste new results into test
    print("calculation_data_exp = ", calculation_data)
    print("values_exp = ", values)
    print("res_emission_mass_exp = ", res_emission_mass)

    calculation_data_exp = {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "main_export_process_chain": [
            {
                "CAPEX": 0.591876,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"NG-G": 0.040812},
                "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                "CONV": {"EL": 0.476859, "IOP-S": 1.373737},
                "EFF": 0.320004,
                "EF_E": {"CH4-G": 201.0, "EL": 402.0, "NG-G": 201.0},
                "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS": 0.05,
                "OPEX-F": 0.017756,
                "OPEX-O": 0,
                "process_code": "NG-DRI-C#B",
                "step": "DERIV",
            }
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0.417344,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"STL-S": 0.00396},
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
            "CALOR": 0.0,
            "SPECCOST": {
                "CO2-G": 0.044519,
                "EL": 0.08078,
                "H2O-L": 0.001374,
                "HEAT": 0.0577,
                "IOP-S": 0.0,
                "N2-G": 0.01154,
                "NG-G": 0.0,
            },
            "WACC": 0.0,
        },
        "secondary_process": {},
        "transport_process_chain": [
            {
                "CONV": {},
                "DIST": 999.0,
                "EFF": 1.0,
                "OPEX-O": 0,
                "OPEX-T": 0,
                "process_code": "DRI-SB#B",
                "step": "SHP",
            }
        ],
    }
    values_exp = [
        {
            "emissions": {
                "ch4_direct_co2e_e": 274.374044,
                "ch4_direct_co2e_m": 274.374044,
                "ch4_direct_e": 9.207183,
                "ch4_direct_m": 9.207183,
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_last_proc_e": 0.0,
                "co2_bound_in_product_last_proc_m": 0.0,
                "co2_bound_in_product_m": 148.05785,
                "co2_captured_e": 239.851022,
                "co2_captured_m": 239.851022,
                "co2_direct_e": 204.315874,
                "co2_direct_m": 204.315874,
                "co2_in_flows_e": 592.224746,
                "co2_in_flows_m": 592.224746,
                "co2_indirect_scope2_e": 189.780347,
                "co2_indirect_scope2_m": 189.780347,
                "co2e_total_direct_e": 478.689918,
                "co2e_total_direct_m": 478.689918,
            },
            "flows": {"EL": 0.47209, "IOP-S": 1.36},
            "main_input": 3.093711,
            "main_output": 0.99,
            "process_code": "NG-DRI-C#B",
            "process_step": "DERIV",
        },
        {
            "emissions": {
                "ch4_direct_co2e_e": 0.0,
                "ch4_direct_co2e_m": 0.0,
                "ch4_direct_e": 0.0,
                "ch4_direct_m": 0.0,
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_bound_in_product_m": 148.05785,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 0.0,
                "co2_direct_m": 0.0,
                "co2_in_flows_e": 0.0,
                "co2_in_flows_m": 0.0,
                "co2_indirect_scope2_e": 0.0,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 0.0,
                "co2e_total_direct_m": 0.0,
            },
            "flows": {},
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
                "co2_bound_in_product_e": 14.511207,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_bound_in_product_m": 14.511207,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 133.546643,
                "co2_direct_m": 134.350643,
                "co2_in_flows_e": 0.0,
                "co2_in_flows_m": 0.804,
                "co2_indirect_scope2_e": 195.3,
                "co2_indirect_scope2_m": 195.3,
                "co2e_total_direct_e": 133.919131,
                "co2e_total_direct_m": 134.723131,
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
            "gas_type": "CO2",
            "process_subtype": "Bound in product",
            "values": 14511.207328,
        },
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
            "values": 134350.642522,
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
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
    ]

    assert _rec_approx(calculation_data) == calculation_data_exp
    assert _rec_approx(values) == values_exp
    assert _rec_approx(res_emission_mass) == res_emission_mass_exp


@pytest.mark.parametrize(
    "scenario, kwargs, api_kwargs",
    [
        [
            "2040 (medium)",
            {
                "chain_name": "STL-S__NG-DRI-C_EAF__prod_in_supply",
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
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_supply",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
        ],
    ],
)
def test_new_blue_chain_real_data(scenario, kwargs, api_kwargs):
    """Data test for blue iron chain using current data."""
    data_handler = DataHandler(
        data_dir=DEFAULT_DATA_DIR,
        scenario=scenario,
        tool_version_color="blue",
    )
    calculation_data = data_handler.get_calculation_data(**kwargs, optimize_flh=False)
    # round and sort for easier comparison
    calculation_data = _sort_nested(_round_nested(calculation_data))

    values, _df_result_cost, _df_result_emissions, _df_result_emissions_mass = (
        PtxCalc.calculate(calculation_data)
    )  # noqa
    # round and sort for easier comparison
    values = _sort_nested(_round_nested(values))

    # test api output
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    api_result = api.calculate(  # noqa
        scenario=scenario,
        **api_kwargs,
        tool_version_color="blue",
        optimize_flh=False,
    )

    res_emission_mass = api_result.emission_mass[
        ["process_subtype", "emission_type", "gas_type", "values"]
    ].to_dict(orient="records")
    # round and sort for easier comparison
    res_emission_mass = _sort_nested(_round_nested(res_emission_mass))

    # print so we can copy/paste new results into test
    print("calculation_data_exp = ", calculation_data)
    print("values_exp = ", values)
    print("res_emission_mass_exp = ", res_emission_mass)

    calculation_data_exp = {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "main_export_process_chain": [
            {
                "CAPEX": 0,
                "CH4SHARE": {"NG-G": 0.909},
                "CONV": {"DIESEL-L": 0.000595, "EL": 0.001153, "NG-G": 1.00378},
                "EFF": 0.986425,
                "EF_E": {"DIESEL-L": 266.76, "NG-G": 201.0},
                "EF_M": {"DIESEL-L": 266.76, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS_FLOW": {"NG-G": 0.00378},
                "OPEX-F": 0,
                "OPEX-O": 0.004863,
                "process_code": "NG-PROD#B",
                "step": "NG_PROD",
            },
            {
                "CAPEX": 0.591876,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"NG-G": 0.040812},
                "CO2CPT-R": {"CH4-G": 0.9, "NG-G": 0.9},
                "CO2CPT-S": {"CH4-G": 0.45, "NG-G": 0.45},
                "CONV": {"EL": 0.476859, "IOP-S": 1.373737},
                "EFF": 0.336004,
                "EF_E": {"CH4-G": 201.0, "NG-G": 201.0},
                "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20.0,
                "OPEX-F": 0.017756,
                "OPEX-O": 0,
                "process_code": "NG-DRI-C#B",
                "step": "DERIV",
            },
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0.417344,
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
                "EL": 0.08078,
                "H2O-L": 0.001374,
                "HEAT": 0.0577,
                "IOP-S": 0.267076,
                "N2-G": 0.01154,
                "NG-G": 0,
            },
            "WACC": 0.0487,
        },
        "secondary_process": {},
        "transport_process_chain": [
            {
                "CONV": {},
                "DIST": 12830.0,
                "EFF": 1.0,
                "OPEX-O": 0,
                "OPEX-T": 0.0,
                "process_code": "DRI-SB#B",
                "step": "SHP",
            }
        ],
    }
    values_exp = [
        {
            "emissions": {
                "ch4_direct_co2e_e": 20.74269,
                "ch4_direct_co2e_m": 20.74269,
                "ch4_direct_e": 0.696063,
                "ch4_direct_m": 0.696063,
                "co2_bound_in_product_e": 0.0,
                "co2_bound_in_product_last_proc_e": 0.0,
                "co2_bound_in_product_last_proc_m": 0.0,
                "co2_bound_in_product_m": 0.0,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 592.692757,
                "co2_direct_m": 592.692757,
                "co2_in_flows_e": 592.692757,
                "co2_in_flows_m": 592.692757,
                "co2_indirect_scope2_e": 0.0,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 613.435447,
                "co2e_total_direct_m": 613.435447,
            },
            "flows": {"DIESEL-L": 0.001753, "EL": 0.003397, "NG-G": 2.957531},
            "main_input": 2.986941,
            "main_output": 2.946394,
            "process_code": "NG-PROD#B",
            "process_step": "NG_PROD",
        },
        {
            "emissions": {
                "ch4_direct_co2e_e": 0.0,
                "ch4_direct_co2e_m": 0.0,
                "ch4_direct_e": 0.0,
                "ch4_direct_m": 0.0,
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_last_proc_e": 0.0,
                "co2_bound_in_product_last_proc_m": 0.0,
                "co2_bound_in_product_m": 148.05785,
                "co2_captured_e": 239.851165,
                "co2_captured_m": 239.851165,
                "co2_direct_e": 204.316084,
                "co2_direct_m": 204.316084,
                "co2_in_flows_e": 592.225098,
                "co2_in_flows_m": 592.225098,
                "co2_indirect_scope2_e": 0.0,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 204.316084,
                "co2e_total_direct_m": 204.316084,
            },
            "flows": {"EL": 0.47209, "IOP-S": 1.36},
            "main_input": 2.946394,
            "main_output": 0.99,
            "process_code": "NG-DRI-C#B",
            "process_step": "DERIV",
        },
        {
            "emissions": {
                "ch4_direct_co2e_e": 0.0,
                "ch4_direct_co2e_m": 0.0,
                "ch4_direct_e": 0.0,
                "ch4_direct_m": 0.0,
                "co2_bound_in_product_e": 148.05785,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_bound_in_product_m": 148.05785,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 0.0,
                "co2_direct_m": 0.0,
                "co2_in_flows_e": 0.0,
                "co2_in_flows_m": 0.0,
                "co2_indirect_scope2_e": 0.0,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 0.0,
                "co2e_total_direct_m": 0.0,
            },
            "flows": {},
            "main_input": 0.99,
            "main_output": 0.99,
            "process_code": "DRI-SB#B",
            "process_step": "SHP",
        },
        {
            "emissions": {
                "ch4_direct_co2e_e": 0.0,
                "ch4_direct_co2e_m": 0.0,
                "ch4_direct_e": 0.0,
                "ch4_direct_m": 0.0,
                "co2_bound_in_product_e": 0.0,
                "co2_bound_in_product_last_proc_e": 148.05785,
                "co2_bound_in_product_last_proc_m": 148.05785,
                "co2_bound_in_product_m": 0.0,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 208.35785,
                "co2_direct_m": 208.35785,
                "co2_in_flows_e": 60.3,
                "co2_in_flows_m": 60.3,
                "co2_indirect_scope2_e": 65.1,
                "co2_indirect_scope2_m": 65.1,
                "co2e_total_direct_e": 208.35785,
                "co2e_total_direct_m": 208.35785,
            },
            "flows": {"EL": 0.651, "NG-G": 0.3},
            "main_input": 0.99,
            "main_output": 1.0,
            "process_code": "EAF#B",
            "process_step": "DERIV_I2",
        },
    ]
    res_emission_mass_exp = [
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "Bound in product",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "EAF#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "EAF#B",
            "values": 208356.44926,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "EAF#B",
            "values": 65100.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "NG-DRI-C#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "NG-DRI-C#B",
            "values": 204317.899955,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "NG-DRI-C#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "NG-PROD#B",
            "values": 20742.71451,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "NG-PROD#B",
            "values": 592693.107938,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "NG-PROD#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CH4",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
        {
            "emission_type": "direct",
            "gas_type": "CO2",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
        {
            "emission_type": "indirect",
            "gas_type": "CO2",
            "process_subtype": "DRI-SB#B",
            "values": 0.0,
        },
    ]

    assert _rec_approx(calculation_data) == calculation_data_exp
    assert _rec_approx(values) == values_exp
    assert _rec_approx(res_emission_mass) == res_emission_mass_exp
