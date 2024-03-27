# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging

import pandas as pd
import pytest

from flh_opt.api_opt import get_profiles_and_weights, optimize

logging.basicConfig(level=logging.INFO)


# borrowed from test_api_data.py:
# TODO: make this available globally
def rec_approx(x):
    if isinstance(x, dict):
        return {k: rec_approx(v) for k, v in x.items()}
    elif isinstance(x, list):
        return [rec_approx(v) for v in x]
    elif isinstance(x, (int, float)):
        return pytest.approx(x)
    else:
        return x


api_test_settings = [
    {
        "id": "H2, PV",
        "SOURCE_REGION_CODE": "ARG",
        "RES": [
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.1,
                "PROCESS_CODE": "PV-FIX",
            }
        ],
        "ELY": {
            "EFF": 0.75,
            "CAPEX_A": 25,
            "OPEX_F": 5,
            "OPEX_O": 0.1,
            "CONV": {"H2O-L": 0.1},
        },
        "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "SPECCOST": {"H2O-L": 1, "CO2-G": 1, "HEAT": 1},
        "expected_output": {
            "RES": [
                {
                    "PROCESS_CODE": "PV-FIX",
                    "FLH": 0.10209904130397318,
                    "SHARE_FACTOR": 1.0,
                }
            ],
            "ELY": {"FLH": 0.36068215977942414},
            "EL_STR": {"CAP_F": 121.50878141391004},
            "H2_STR": {"CAP_F": 348.33524817139295},
        },
        "expected_ojective_value": 2480.8292413355575,
    },
    {
        "id": "CH4, hybrid",
        "SOURCE_REGION_CODE": "ARG",
        "RES": [
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.01,
                "PROCESS_CODE": "PV-FIX",
            },
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.02,
                "PROCESS_CODE": "WIND-ON",
            },
        ],
        "ELY": {
            "EFF": 0.75,
            "CAPEX_A": 25,
            "OPEX_F": 5,
            "OPEX_O": 0.1,
            "CONV": {"H2O-L": 0.1},
        },
        "DERIV": {
            "EFF": 0.8,
            "CAPEX_A": 0.826,
            "OPEX_F": 0.209,
            "OPEX_O": 0.025,
            "PROCESS_CODE": "CH4SYN",
        },
        "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "SPECCOST": {"H2O-L": 1, "CO2-G": 1, "HEAT": 1},
        "expected_output": {
            "RES": [
                {"PROCESS_CODE": "PV-FIX", "FLH": 0, "SHARE_FACTOR": -0.0},
                {
                    "PROCESS_CODE": "WIND-ON",
                    "FLH": 0.345701024478453,
                    "SHARE_FACTOR": 1.0,
                },
            ],
            "ELY": {"FLH": 0.5124598171364299},
            "EL_STR": {"CAP_F": -0.0},
            "H2_STR": {"CAP_F": 122.44991931269928},
        },
        "expected_ojective_value": 1748.871332914744,
    },
    {
        "id": "H2, hybrid",
        "SOURCE_REGION_CODE": "ARG",
        "RES": [
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.01,
                "PROCESS_CODE": "PV-FIX",
            },
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.02,
                "PROCESS_CODE": "WIND-ON",
            },
        ],
        "ELY": {
            "EFF": 0.75,
            "CAPEX_A": 25,
            "OPEX_F": 5,
            "OPEX_O": 0.1,
            "CONV": {"H2O-L": 0.1},
        },
        "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "SPECCOST": {"H2O-L": 1, "CO2-G": 1, "HEAT": 1},
        "expected_output": {
            "RES": [
                {"PROCESS_CODE": "PV-FIX", "FLH": 0, "SHARE_FACTOR": -0.0},
                {
                    "PROCESS_CODE": "WIND-ON",
                    "FLH": 0.345701024478453,
                    "SHARE_FACTOR": 1.0,
                },
            ],
            "ELY": {"FLH": 0.5124598171364299},
            "EL_STR": {"CAP_F": -0.0},
            "H2_STR": {"CAP_F": 122.44991931269928},
        },
        "expected_ojective_value": 1748.871332914744,
    },
]
# Corresponding names for each configuration
api_test_settings_names = []
for i in api_test_settings:
    api_test_settings_names.append(i["id"])


@pytest.fixture(scope="module", params=api_test_settings, ids=api_test_settings_names)
def call_optimize(request):
    input_data = request.param
    [res, n] = optimize(input_data)
    return [res, n, input_data]


def test_optimize_optimal_solution(call_optimize):
    """Test if solver finds optimal solution."""
    [res, n, input_data] = call_optimize
    assert res["model_status"][0] == "ok", "Solver status not OK"
    assert res["model_status"][1] == "optimal", "No optimal solution found"


def test_optimize_export_to_netcdf(call_optimize):
    """Write network to netcdf file."""
    [res, n, input_data] = call_optimize
    n.export_to_netcdf(f"tests/{input_data['id']}.nc")


def test_optimize_expected_results(call_optimize):
    """Test if obtained results match expected results."""
    [res, n, input_data] = call_optimize

    # Test for expected objective value:
    assert n.objective == pytest.approx(input_data["expected_ojective_value"])

    # Test for other results:
    assert rec_approx(res) == input_data["expected_output"]


# settings for profile tests:
profile_test_settings = [
    {
        "source_region_code": "ARG",
        "re_location": "PV-FIX",
        "selection": None,
        "expected_sum": pd.Series({"PV-FIX": 215.495714}),
        "expected_weights_sum": 8760,
    },
    {
        "source_region_code": "ARG",
        "re_location": "RES_HYBR",
        "selection": range(0, 48),
        "expected_sum": pd.Series({"PV-FIX": 10.133478, "WIND-ON": 30.832906}),
        "expected_weights_sum": 486.857143,
    },
]


@pytest.mark.parametrize("settings", profile_test_settings)
def test_profile_import(settings):
    res, weights = get_profiles_and_weights(
        source_region_code=settings["source_region_code"],
        re_location=settings["re_location"],
        selection=settings["selection"],
    )
    if settings["selection"] is not None:
        assert len(res) == len(settings["selection"])

    pd.testing.assert_series_equal(res.sum(), settings["expected_sum"])
    assert settings["expected_weights_sum"] == pytest.approx(weights["weight"].sum())
