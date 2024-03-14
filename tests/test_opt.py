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
        "SOURCE_REGION_CODE": "ARG",
        "RES": [
            {
                "CAPEX_A": 30,
                "OPEX_F": 1,
                "OPEX_O": 0.1,
                "PROCESS_CODE": "PV-FIX",
            }
        ],
        "ELY": {"EFF": 0.75, "CAPEX_A": 25, "OPEX_F": 5, "OPEX_O": 0.1},
        "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "SPECCOST": {"H2O": 0.658},
        "expected_output": {
            "RES": [
                {
                    "SHARE_FACTOR": 1,
                    "FLH": 0.230310775525,
                    "PROCESS_CODE": "PV-FIX",
                }
            ],
            "ELY": {"FLH": 0.40971534364341405},
            "EL_STR": {"CAP_F": 0},
            "H2_STR": {"CAP_F": 34.57725460457206},
        },
        "expected_ojective_value": 391.21301357978956,
    },
    {
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
        "ELY": {"EFF": 0.75, "CAPEX_A": 25, "OPEX_F": 5, "OPEX_O": 0.1},
        "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
        "SPECCOST": {"H2O": 0.658},
        "expected_output": {
            "RES": [
                {
                    "SHARE_FACTOR": 0.3580517435075871,
                    "FLH": 0.21534125023157286,
                    "PROCESS_CODE": "PV-FIX",
                },
                {
                    "SHARE_FACTOR": 0.6419482564924128,
                    "FLH": 0.11585990924307125,
                    "PROCESS_CODE": "WIND-ON",
                },
            ],
            "ELY": {"FLH": 0.8545957682852908},
            "EL_STR": {"CAP_F": 0},
            "H2_STR": {"CAP_F": 12.323994361813343},
        },
        "expected_ojective_value": 198.36220457417505,
    },
]


@pytest.mark.parametrize("input_data", api_test_settings)
def test_api_opt(input_data):

    [res, n] = optimize(input_data)

    # write to netcdf file:
    n.export_to_netcdf("tmp.nc")

    # Test for expected objective value:
    assert n.objective == pytest.approx(input_data["expected_ojective_value"])

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
    assert settings["expected_weights_sum"] == pytest.approx(weights.sum())
