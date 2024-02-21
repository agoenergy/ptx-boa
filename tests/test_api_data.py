# -*- coding: utf-8 -*-
"""Unittests for ptxboa api_data module."""
from pathlib import Path

import pandas as pd
import pytest

from ptxboa.api_data import DataHandler


@pytest.fixture()
def user_data_01():
    return pd.DataFrame(
        data=[
            ("Australia", "PV tilted", 800, "CAPEX", None),
            ("Chile", "PV tilted", 900, "CAPEX", None),
            ("Chile", "Wind Offshore", 5000, "full load hours", None),
            ("Argentina", "PV tilted", 2000, "full load hours", None),
            ("Costa Rica", "Wind-PV-Hybrid", 2000, "full load hours", None),
            ("Australia", "Wind Onshore", 4000, "full load hours", None),
            ("Costa Rica", None, 0.12, "interest rate", None),
        ],
        columns=[
            "source_region_code",
            "process_code",
            "value",
            "parameter_code",
            "flow_code",
        ],
    )


@pytest.fixture()
def ptxdata_dir_static():
    """Instance with static copy of the data, this dataset will never change."""
    return Path(__file__).parent / "test_data"


@pytest.fixture()
def ptxdata_dir_live():
    """
    Instance with live data as used in deployment.

    This dataset could change and we might use this fixture to see if updates work
    correctly.
    """
    return None


@pytest.mark.parametrize(
    "scenario, parameter_code, process_code, flow_code, source_region_code, target_country_code, process_code_res, process_code_ely, process_code_deriv, user_data, expected, default",  # noqa
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
            None,  # default
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
            None,  # default
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
            None,  # default
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
            None,  # default
        ),
        (
            "2030 (low)",  # scenario
            "FLH",  # parameter_code
            "PV-TRK",  # process_code
            "",  # flow_code
            "SWE",  # source_region_code
            "",  # target_country_code
            "PEM-EL",  # process_code
            "",  # process_code_ely
            "",  # process_code_deriv
            None,  # user_data
            8760,  # expected: default value
            8760,  # default
        ),
    ),
)
@pytest.mark.parametrize("ptxdata_dir", ("ptxdata_dir_static", "ptxdata_dir_live"))
def test_get_parameter_value(
    ptxdata_dir,
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
    default,
):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)

    if user_data is not None:
        user_data = request.getfixturevalue(user_data)

    data_handler = DataHandler(
        scenario=scenario,
        user_data=user_data,
        data_dir=ptxdata_dir,
    )
    result = data_handler._get_parameter_value(
        parameter_code=parameter_code,
        process_code=process_code,
        flow_code=flow_code,
        source_region_code=source_region_code,
        target_country_code=target_country_code,
        process_code_res=process_code_res,
        process_code_ely=process_code_ely,
        process_code_deriv=process_code_deriv,
        default=default,
    )

    assert expected == pytest.approx(result)


@pytest.mark.parametrize(
    "dimension, parameter_name, expected_code",
    (
        ("country", "Germany", "DEU"),
        ("country", "", ""),
        ("country", None, ""),
        ("secproc_water", "Specific costs", ""),
    ),
)
def test_get_dimensions_parameter_code(dimension, parameter_name, expected_code):
    out_code = DataHandler.get_dimensions_parameter_code(dimension, parameter_name)
    assert out_code == expected_code
