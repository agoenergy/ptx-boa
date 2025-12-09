"""Unittests for blue hydrogen version."""

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
                value = dim.loc[value, dimname + "_name"]
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
                "process_code": "NG-DRI",
                "parameter_code": "LKG",
                "value": 0.2,
            },
            {
                "process_code": "EAF",
                "parameter_code": "EFF",
                "value": 0.9,
            },
            {
                "process_code": "NG-DRI",
                "flow_code": "EL",
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

    assert _rec_approx(calculation_data) == {
        "flh_opt_process": {},
        "main_process_chain": [
            {
                "EFF": 0.8,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {"EL": 0.3},
                "step": "DERIV",
                "process_code": "NG-DRI",
            }
        ],
        "transport_process_chain": [
            {
                "DIST": 2668.15,
                "EFF": 1.0,
                "OPEX-T": 3.765382979887925e-07,
                "OPEX-O": 0,
                "CONV": {},
                "step": "SHP",
                "process_code": "DRI-SB",
            },
            {
                "EFF": 0.9,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "POST",
                "process_code": "EAF",
            },
        ],
        "secondary_process": {},
        "parameter": {
            "WACC": 0.0826130467109222,
            "CALOR": 1.0,
            "SPECCOST": {
                "HEAT": 0.0577,
                "EL": 0.08078,
                "CO2-G": 0.0445186199587845,
                "H2O-L": 0.0013737954502618,
                "N2-G": 0.01154,
            },
        },
        "context": {"source_region_code": "MAR", "target_country_code": "DEU"},
    }

    values, _cost_result_df = PtxCalc.calculate(calculation_data)  # noqa
    # TODO: our output is only cost, we need to restructure
    # calculation module to also get flow values
    assert _rec_approx(values) == [
        {"process_step": "DERIV", "main_output": 0.8, "flows": {"EL": 0.24}},
        {"process_step": "SHP", "main_output": 0.8, "flows": {}},
        {"process_step": "POST", "main_output": 0.72, "flows": {}},
    ]
