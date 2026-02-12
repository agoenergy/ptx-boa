"""Unittests for blue hydrogen version."""

from pprint import pprint

import pandas as pd
import pytest

from ptxboa.api import PtxCalc
from ptxboa.api_data import DataHandler
from tests.test_api import ptxdata_dir_static


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
    "scenario, kwargs",
    [
        [
            "2040 (medium)",
            {
                "chain_name": "Blue Iron (blue)",
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
def test_new_blue_chain(scenario, kwargs, request):
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
                "process_code": "NG-DRI",
                "flow_code": "NG-G",  # main flow in
                "parameter_code": "LOSS",
                "value": 0.05,  # process_calc!E7
            },
            {
                "process_code": "NG-DRI",
                "parameter_code": "EFF",
                "value": 0.336004,  # process_calc!E3
            },
            {
                "process_code": "NG-DRI",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.476859,  # process_calc!E4
            },
            {
                "process_code": "NG-DRI",
                "flow_code": "IOP-S",
                "parameter_code": "CONV",
                "value": 0.99,  # process_calc!E5
            },
            {
                "process_code": "NG-DRI",
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
                "process_code": "NG-DRI",
                "parameter_code": "CO2CPT-S",
                "value": 0.45,  # process_calc!E10
            },
            {
                "process_code": "NG-DRI",
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
        data_dir=ptxdata_dir_static, scenario=scenario, user_data=user_data
    )
    calculation_data = data_handler.get_calculation_data(**kwargs, optimize_flh=False)
    values, _cost_result_df = PtxCalc.calculate(calculation_data)  # noqa

    pprint(calculation_data)
    pprint(values)

    assert _rec_approx(calculation_data) == {
        "context": {"source_region_code": "QAT", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "parameter": {
            "CALOR": 0.0,
            "SPECCOST": {
                "NG-G": 0.0,
                "CO2-G": 0.0445186199587845,
                "EL": 0.08078,
                "H2O-L": 0.0013737954502618,
                "HEAT": 0.0577,
                "IOP-S": 0.0,
                "N2-G": 0.01154,
            },
            "WACC": 0,
        },
        "main_export_process_chain": [
            {
                "CAPEX": 0,
                "CONV": {"EL": 0.476859, "IOP-S": 0.99, "HEAT": 0.01},
                "EFF": 0.3200038095238095,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "LOSS": 0.05,
                "CO2CPT-R": 0.9,
                "CO2CPT-S": 0.45,
                "process_code": "NG-DRI",
                "step": "DERIV",
                "CH4SHARE": {"NG-G": 0.909},
                "CO2BOUND": {
                    "NG-G": 0.0408116143367898,
                },
                "EF_M": {"NG-G": 201.0},
            }
        ],
        "secondary_process": {},
        "transport_process_chain": [
            {
                "CONV": {},
                "DIST": 999,
                "EFF": 1.0,
                "OPEX-O": 0,
                "OPEX-T": 3.765382979887925e-07,
                "process_code": "DRI-SB",
                "step": "SHP",
            }
        ],
        "main_import_process_chain": [
            {
                "CAPEX": 0,
                "CONV": {"NG-G": 0.315, "EL": 0.651, "HEAT": 0.01},
                "EFF": 1.010101,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "LOSS_FLOW": {"NG-G": 0.05},
                "CH4SHARE": {
                    "NG-G": 0.909,
                },
                "EF_M": {
                    "NG-G": 201.0,
                },
                "CO2BOUND": {
                    "NG-G": 0.0408116143367898,
                    "STL-S": 0.00396,
                },
                "process_code": "EAF",
                "step": "DERIV_I",
            },
        ],
    }

    assert _rec_approx(values) == [
        {
            "flows": {
                "EL": 0.4720904147209042,  # process_calc!E26
                "IOP-S": 0.9801000098010001,  # process_calc!E27
                "HEAT": 0.0099,  # process_calc!E28
            },
            "main_input": 3.0937132010184407,  # process_calc!E25
            "main_output": 0.99,  # process_calc!E33
            "process_step": "DERIV",
            "emissions": {
                "co2_bound_output": 0.0,
                "co2_captured": -0.04870006586817431,
                "co2_emission_direct": 0.006012353810885717,
                "co2_emission_from_bound": -0.07154701034954002,
                "co2_indirect": 0.0,
                "co2e_emission_direct": 3.996637207707444,
            },
        },
        {
            "flows": {},
            "main_input": 0.99,
            "main_output": 0.99,
            "process_step": "SHP",
            "emissions": {
                "co2_bound_output": 0.0,
                "co2_captured": 0.0,
                "co2_emission_direct": 0.0,
                "co2_emission_from_bound": 0.0,
                "co2_indirect": 0.0,
                "co2e_emission_direct": 0.0,
            },
        },
        {
            "flows": {
                "NG-G": 0.315,  # process_calc!J26
                "EL": 0.651,  # process_calc!J27
                "HEAT": 0.01,  # process_calc!J30
            },
            "main_input": 0.99,  # process_calc!J25
            "main_output": 1.0,
            "process_step": "DERIV_I",
            "emissions": {
                "co2_bound_output": 0.00396,
                "co2_captured": -0.0,
                "co2_emission_direct": 0.0006121742150518469,
                "co2_emission_from_bound": -0.008283484301036939,
                "co2_indirect": 63.315,
                "co2e_emission_direct": 0.0006121742150518469,
            },
        },
    ]
