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
    }

    [res, n] = optimize(input_data)

    # write to netcdf file:
    n.export_to_netcdf("tmp.nc")

    # Test for expected objective value:
    assert n.objective == pytest.approx(3046.20318251384)

    assert rec_approx(res) == {
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
