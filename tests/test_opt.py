# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging

import pytest

from flh_opt.api_opt import get_profiles, optimize

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


def test_api_opt():
    input_data = {
        "SOURCE_REGION_CODE": "GYE",
        "RES": [
            {
                "CAPEX_A": 0.826,
                "OPEX_F": 0.209,
                "OPEX_O": 0.025,
                "PROCESS_CODE": "PV-FIX",
            }
        ],
        "ELY": {"EFF": 0.834, "CAPEX_A": 0.52, "OPEX_F": 0.131, "OPEX_O": 0.2},
        "EL_STR": {"EFF": 0.544, "CAPEX_A": 0.385, "OPEX_F": 0.835, "OPEX_O": 0.501},
        "H2_STR": {"EFF": 0.478, "CAPEX_A": 0.342, "OPEX_F": 0.764, "OPEX_O": 0.167},
        "SPECCOST": {"H2O": 0.658},
    }

    [res, n] = optimize(input_data)

    # write to netcdf file:
    n.export_to_netcdf("tmp.nc")

    # Test for expected objective value:
    assert n.objective == pytest.approx(2.29136690647482)

    assert rec_approx(res) == {
        "RES": [
            {
                "SHARE_FACTOR": 1,
                "FLH": 1,
                "PROCESS_CODE": "PV-FIX",
            }
        ],
        "ELY": {"FLH": 1},
        "EL_STR": {"CAP_F": 0},
        "H2_STR": {"CAP_F": 0},
    }


def test_profile_import():
    res = get_profiles(
        source_region_code="ARG",
        process_code="PV-FIX",
        re_location="PV-FIX",
        selection=range(0, 48),
    )
    assert len(res) == 48
    assert 11.756292238271236 == pytest.approx(res.sum())
