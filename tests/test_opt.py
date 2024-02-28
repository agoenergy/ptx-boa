# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging

import pytest

from flh_opt.api_opt import optimize

logging.basicConfig(level=logging.INFO)


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

    # Test for expected objective value:
    assert n.objective == pytest.approx(2.29136690647482)

    logging.info(res)

    # write to netcdf file:
    n.export_to_netcdf("tmp.nc")
