"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa.api import PtxboaAPI, PtxCalc
from ptxboa.api_data import DataHandler
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
def test_new_blue_chain(scenario, kwargs, api_kwargs):
    """Data test for blue iron chain."""
    user_data = pd.DataFrame(
        [
            # FIXME: all flows are (in green tool) expected to have CALOR
            # but doesit make sense for Steel?
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
                "parameter_code": "CO2CPT-R",
                "flow_code": "NG-G",
                "value": 0.9,  # process_calc!E14
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CO2BOUND",
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
    values, _df_result_cost, _df_result_emissions, _df_result_emissions_mass = (
        PtxCalc.calculate(calculation_data)
    )  # noqa

    # round and sort for easier comparison
    calculation_data = _sort_nested(_round_nested(calculation_data))
    print(calculation_data)

    assert _rec_approx(calculation_data) == {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "main_export_process_chain": [
            {
                "CAPEX": 0,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"NG-G": 0.040812},
                "CONV": {"EL": 0.476859, "IOP-S": 1.373737},
                "EFF": 0.320004,
                "EF_E": {"EL": 402.0, "NG-G": 201.0},
                "EF_M": {"CH4-G": 201.0, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS": 0.05,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "NG-DRI-C#B",
                "step": "DERIV",
            }
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"NG-G": 0.040812, "STL-S": 0.00396},
                "CONV": {"EL": 0.651, "NG-G": 0.0042},
                "EFF": 1.010101,
                "EF_E": {"EL": 300.0},
                "EF_M": {"NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS_FLOW": {"NG-G": 0.05},
                "OPEX-F": 0,
                "OPEX-O": 0,
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
    # round and sort for easier comparison
    values = _sort_nested(_round_nested(values))
    print(values)

    assert _rec_approx(values) == [
        {
            "emissions": {
                "ch4_direct_co2e_e": 3.990625,
                "ch4_direct_co2e_m": 3.990625,
                "ch4_direct_e": 0.133914,
                "ch4_direct_m": 0.133914,
                "co2_bound_in_product_e": 0.0,
                "co2_bound_in_product_last_proc_e": 0.0,
                "co2_bound_in_product_last_proc_m": 0.0,
                "co2_bound_in_product_m": 0.0,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": 0.0,
                "co2_direct_m": 0.0,
                "co2_in_flows_e": 0.0,
                "co2_in_flows_m": 0.0,
                "co2_indirect_scope2_e": 189.780347,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 3.990625,
                "co2e_total_direct_m": 3.990625,
            },
            "flows": {"EL": 0.47209, "IOP-S": 1.36},
            "main_input": 3.093713,
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
                "co2_bound_in_product_e": 0.0,
                "co2_bound_in_product_last_proc_e": 0.0,
                "co2_bound_in_product_last_proc_m": 0.0,
                "co2_bound_in_product_m": 0.0,
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
                "ch4_direct_co2e_e": 0.005418,
                "ch4_direct_co2e_m": 0.005418,
                "ch4_direct_e": 0.000182,
                "ch4_direct_m": 0.000182,
                "co2_bound_in_product_e": 0.00396,
                "co2_bound_in_product_last_proc_e": 0.00396,
                "co2_bound_in_product_last_proc_m": 0.00396,
                "co2_bound_in_product_m": 0.00396,
                "co2_captured_e": 0.0,
                "co2_captured_m": 0.0,
                "co2_direct_e": -0.00396,
                "co2_direct_m": 0.80004,
                "co2_in_flows_e": 0.0,
                "co2_in_flows_m": 0.804,
                "co2_indirect_scope2_e": 195.3,
                "co2_indirect_scope2_m": 0.0,
                "co2e_total_direct_e": 0.001458,
                "co2e_total_direct_m": 0.805458,
            },
            "flows": {"EL": 0.651, "NG-G": 0.0042},
            "main_input": 0.99,
            "main_output": 1.0,
            "process_code": "EAF#B",
            "process_step": "DERIV_I",
        },
    ]

    # test api output
    api = PtxboaAPI(data_dir=ptxdata_dir_static)
    api_result = api.calculate(  # noqa
        scenario=scenario,
        **api_kwargs,
        user_data=user_data,
        tool_version_color="blue",
        optimize_flh=False,
    )
