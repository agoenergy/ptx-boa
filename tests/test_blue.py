"""Unittests for blue hydrogen version."""

import pytest

from ptxboa.api_data import DataHandler
from tests.test_api import ptxdata_dir_static


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
    data_handler = DataHandler(data_dir=str(ptxdata_dir_static), scenario=scenario)
    data = data_handler.get_calculation_data(**kwargs, optimize_flh=False)

    # recursively use pytest.approx
    def rec_approx(x):
        if isinstance(x, dict):
            return {k: rec_approx(v) for k, v in x.items()}
        elif isinstance(x, list):
            return [rec_approx(v) for v in x]
        elif isinstance(x, (int, float)):
            return pytest.approx(x)
        else:
            return x

    assert rec_approx(data) == {
        "context": {
            "source_region_code": "MAR",
            "target_country_code": "DEU",
        },
        "flh_opt_process": {},
        "main_process_chain": [
            {
                "CAPEX": 0,
                "CONV": {},
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "NG-DRI",
                "step": "DERIV",
            },
        ],
        "parameter": {
            "CALOR": 1.0,
            "SPECCOST": {
                "CO2-G": 0.0445186199587845,
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
                "CONV": {},
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "process_code": "EAF",
                "step": "POST",
            },
        ],
    }
