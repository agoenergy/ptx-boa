# -*- coding: utf-8 -*-
"""Unittests for ptxboa api_data module."""

import pandas as pd
import pytest

from ptxboa.api_data import DataHandler, PtxData


@pytest.fixture()
def user_data_01():
    return pd.DataFrame(
        data=[
            ("Australia", "PV tilted", 800, "CAPEX"),
            ("Chile", "PV tilted", 900, "CAPEX"),
            ("Chile", "Wind Offshore", 5000, "full load hours"),
            ("Argentina", "PV tilted", 2000, "full load hours"),
            ("Costa Rica", "Wind-PV-Hybrid", 2000, "full load hours"),
            ("Australia", "Wind Onshore", 4000, "full load hours"),
            ("Costa Rica", None, 0.12, "interest rate"),
        ],
        columns=["source_region_code", "process_code", "value", "parameter_code"],
    )


@pytest.fixture()
def ptxdata_instance():
    return PtxData()


@pytest.mark.parametrize(
    "scenario, parameter_code, process_code, flow_code, source_region_code, target_country_code, process_code_res, process_code_ely, process_code_deriv, user_data, expected",  # noqa
    (
        (
            "2030 (low)",  # scenario
            "CALOR",  # parameter_code
            "",  # process_code
            "CH3OH-L",  # flow_code
            "",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_code_ely
            "",  # process_code_deriv
            None,  # user_data
            5.527777777777777,  # expected
        ),
        (
            "2030 (low)",  # scenario
            "CALOR",  # parameter_code
            "",  # process_code
            "CH3OH-L",  # flow_code
            "",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_code_ely
            "",  # process_code_deriv
            "user_data_01",  # user_data
            5.527777777777777,  # expected
        ),
        (
            "2030 (low)",  # scenario
            "CAPEX",  # parameter_code
            "PV-FIX",  # process_code
            "",  # flow_code
            "AUS",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_code_ely
            "",  # process_code_deriv
            None,  # user_data
            820.2632050586035,  # expected
        ),
        (
            "2030 (low)",  # scenario
            "CAPEX",  # parameter_code
            "PV-FIX",  # process_code
            "",  # flow_code
            "AUS",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_code_ely
            "",  # process_code_deriv
            "user_data_01",  # user_data
            800,  # expected
        ),
    ),
)
def test_get_parameter_value(
    ptxdata_instance,
    scenario,
    parameter_code,
    process_code,
    flow_code,
    source_region_code,
    target_country_code,
    process_code_res,
    process_code_ely,
    process_code_deriv,
    user_data,
    expected,
    request,
):
    if user_data is not None:
        user_data = request.getfixturevalue(user_data)

    handler = DataHandler(ptxdata_instance, scenario=scenario, user_data=user_data)
    result = handler.get_parameter_value(
        parameter_code=parameter_code,
        process_code=process_code,
        flow_code=flow_code,
        source_region_code=source_region_code,
        target_country_code=target_country_code,
        process_code_res=process_code_res,
        process_code_ely=process_code_ely,
        process_code_deriv=process_code_deriv,
    )
    assert expected == pytest.approx(result)
