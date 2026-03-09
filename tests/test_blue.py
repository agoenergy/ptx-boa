"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa import DEFAULT_DATA_DIR
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
    "scenario, kwargs",
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
        ],
    ],
)
def test_new_blue_chain(scenario, kwargs):
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
                "process_code": "NG-DRI-C",
                "flow_code": "NG-G",  # main flow in
                "parameter_code": "LOSS",
                "value": 0.05,  # process_calc!E7
            },
            {
                "process_code": "NG-DRI-C",
                "parameter_code": "EFF",
                "value": 0.336004,  # process_calc!E3
            },
            {
                "process_code": "NG-DRI-C",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.476859,  # process_calc!E4
            },
            {
                "process_code": "NG-DRI-C",
                "flow_code": "IOP-S",
                "parameter_code": "CONV",
                "value": 0.99,  # process_calc!E5
            },
            {
                "process_code": "NG-DRI-C",
                "flow_code": "HEAT",
                "parameter_code": "CONV",
                "value": 0.01,  # process_calc!E6
            },
            {
                "process_code": "EAF",
                "flow_code": "HEAT",
                "parameter_code": "CONV",
                "value": 0.01,  # process_calc!J6
            },
            {
                "process_code": "EAF",
                "parameter_code": "LOSS",
                "flow_code": "NG-G",
                "value": 0.05,  # process_calc!J7
            },
            {
                "process_code": "EAF",
                "parameter_code": "EFF",
                "value": 1.010101,  # process_calc!J3
            },
            {
                "process_code": "EAF",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.651000,  # process_calc!J5
            },
            {
                "process_code": "EAF",
                "flow_code": "NG-G",
                "parameter_code": "CONV",
                "value": 0.3,  # process_calc!J4
            },
            {
                "process_code": "NG-DRI-C",
                "parameter_code": "CO2CPT-S",
                "value": 0.45,  # process_calc!E10
            },
            {
                "process_code": "NG-DRI-C",
                "parameter_code": "CO2CPT-R",
                "value": 0.9,  # process_calc!E13
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CO2BOUND",
                "value": 0.0408116143367898,  # process_calc!E16
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CH4SHARE",
                "value": 0.909,  # process_calc!E18
            },
            {
                "flow_code": "STL-S",
                "parameter_code": "CO2BOUND",
                "value": 0.00396,  # process_calc!J16
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "NG-G",
                "value": 201,  # emission_factors!D7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "EL",
                "source_region_code": "QAT",
                "value": 402,  # emission_factors!E7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "HEAT",
                "source_region_code": "QAT",
                "value": 250,  # emission_factors!G7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "EL",
                "target_country_code": "DEU",
                "value": 300,  # emission_factors!F7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "HEAT",
                "target_country_code": "DEU",
                "value": 250,  # emission_factors!H7
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
    values, _cost_result_df = PtxCalc.calculate(calculation_data)  # noqa

    # round and sort for easier comparison
    calculation_data = _sort_nested(_round_nested(calculation_data))
    print(calculation_data)

    assert _rec_approx(calculation_data) == {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "main_export_process_chain": [
            {
                "CAPEX": 0,
                "CO2CPT-R": 0.9,
                "CO2CPT-S": 0.45,
                "CONV": {"EL": 0.476859, "IOP-S": 0.99},
                "EFF": 0.336004,
                "EF_M": {"EL": 402.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "NG-DRI-C",
                "step": "DERIV",
            }
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0,
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {"NG-G": 0.040812, "STL-S": 0.00396},
                "CONV": {"EL": 0.651, "NG-G": 0.315},
                "EFF": 1.010101,
                "EF_M": {"EL": 402.0, "NG-G": 201.0},
                "FLH": 7000,
                "LIFETIME": 20,
                "LOSS_FLOW": {"NG-G": 0.05},
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "EAF",
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
                "OPEX-T": 0.0,
                "process_code": "DRI-SB",
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
                "co2_bound_output": 0.0,
                "co2_captured": 0.0,
                "co2_emission_direct": 0.0,
                "co2_emission_from_bound": 0.0,
                "co2_indirect": 189.780347,
                "co2e_emission_direct": 0.0,
            },
            "flows": {"EL": 0.47209, "IOP-S": 0.9801},
            "main_input": 2.946394,
            "main_output": 0.99,
            "process_code": "NG-DRI-C",
            "process_step": "DERIV",
        },
        {
            "emissions": {
                "co2_bound_output": 0.0,
                "co2_captured": 0.0,
                "co2_emission_direct": 0.0,
                "co2_emission_from_bound": 0.0,
                "co2_indirect": 0.0,
                "co2e_emission_direct": 0.0,
            },
            "flows": {},
            "main_input": 0.99,
            "main_output": 0.99,
            "process_code": "DRI-SB",
            "process_step": "SHP",
        },
        {
            "emissions": {
                "co2_bound_output": 0.00396,
                "co2_captured": -0.0,
                "co2_emission_direct": 0.000612,
                "co2_emission_from_bound": -0.008283,
                "co2_indirect": 325.017,
                "co2e_emission_direct": 0.000612,
            },
            "flows": {"EL": 0.651, "NG-G": 0.315},
            "main_input": 0.99,
            "main_output": 1.0,
            "process_code": "EAF",
            "process_step": "DERIV_I",
        },
    ]


if __name__ == "__main__":
    # TODO: convert into test function after
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)

    res = api.calculate(
        scenario="2030 (medium)",
        secproc_co2=None,
        secproc_water=None,
        chain="STL-S__NG-DRI-C-C_EAF__prod_in_demand",
        res_gen=None,
        region="Qatar",
        country="Germany",
        transport="Ship",
        ship_own_fuel=False,
        tool_version_color="blue",
    )

    for x in res.todo_results_flows:
        pprint(_sort_nested(_round_nested(x)))
