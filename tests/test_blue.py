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
                dim = DataHandler.dimensions[dimname]  # type:ignore
                try:
                    value = dim.loc[value, dimname + "_name"]
                except Exception:
                    raise KeyError(f"{value} not in {dimname}: {dim.index}")
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
                "chain_name": "TODO: Blue Iron",
                "source_region_code": "MAR",
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
            {
                "flow_code": "STL-S",
                "parameter_code": "CALOR",
                "value": 0,
            },
            {
                "flow_code": "CH4-G",
                "parameter_code": "SPECCOST",
                "value": 0,
            },
            {
                "process_code": "NG-DRI",
                "parameter_code": "LKG",
                "value": 0.05,
            },
            {
                "process_code": "NG-DRI",
                "parameter_code": "EFF",
                "value": 0.370370370370,
            },
            {
                "process_code": "EAF",
                "parameter_code": "EFF",
                "value": 1.23456790123,
            },
            {
                "process_code": "NG-DRI",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.5828271604938,
            },
            {
                "process_code": "NG-DRI",
                "flow_code": "CH4-G",
                "parameter_code": "CONV",
                "value": 2.187,
            },
            {
                "process_code": "EAF",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.349333333333,
            },
            {
                "process_code": "EAF",
                "flow_code": "CH4-G",
                "parameter_code": "CONV",
                "value": 0.3,
            },
        ],
        columns=[
            "parameter_code",
            "process_code",
            "flow_code",
            "source_region_code",
            "value",
        ],
    )

    _translate_user_data(user_data)

    data_handler = DataHandler(
        data_dir=ptxdata_dir_static, scenario=scenario, user_data=user_data
    )
    calculation_data = data_handler.get_calculation_data(**kwargs, optimize_flh=False)
    values, _cost_result_df = PtxCalc.calculate(calculation_data)  # noqa

    pprint(calculation_data)
    pprint(values)

    assert _rec_approx(calculation_data) == {
        "context": {"source_region_code": "MAR", "target_country_code": "DEU"},
        "flh_opt_process": {},
        "main_process_chain": [
            {
                "CAPEX": 0,
                "CONV": {"CH4-G": 2.187, "EL": 0.5828271604938},
                "EFF": 0.3518518518515,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "NG-DRI",
                "step": "DERIV",
            }
        ],
        "parameter": {
            "CALOR": 0.0,
            "SPECCOST": {
                "CH4-G": 0.0,
                "CO2-G": 0.0445186199587845,
                "EL": 0.08078,
                "H2O-L": 0.0013737954502618,
                "HEAT": 0.0577,
                "N2-G": 0.01154,
            },
            "WACC": 0.0826130467109222,
        },
        "secondary_process": {},
        "transport_process_chain": [
            {
                "CONV": {},
                "DIST": 2668.15,
                "EFF": 1.0,
                "OPEX-O": 0,
                "OPEX-T": 3.765382979887925e-07,
                "process_code": "DRI-SB",
                "step": "SHP",
            },
            {
                "CAPEX": 0,
                "CONV": {"CH4-G": 0.3, "EL": 0.349333333333},
                "EFF": 1.23456790123,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "EAF",
                "step": "POST",
            },
        ],
    }

    # TODO: our output is only cost, we need to restructure
    # calculation module to also get flow values
    assert _rec_approx(values) == [
        {
            "flows": {"CH4-G": 1.7714700000065544, "EL": 0.47209000000172474},
            "main_output": 0.810000000002997,
            "process_step": "DERIV",
        },
        {"flows": {}, "main_output": 0.810000000002997, "process_step": "SHP"},
        {
            "flows": {"CH4-G": 0.3, "EL": 0.34933333333299993},
            "main_output": 1.0,
            "process_step": "POST",
        },
    ]
