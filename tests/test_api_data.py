# -*- coding: utf-8 -*-
"""Unittests for ptxboa api_data module."""
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from ptxboa.api_data import DataHandler

from .utils import assert_deep_equal


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
            ("Costa Rica", None, 0.12, "WACC", None),
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
@pytest.mark.parametrize("ptxdata_dir", ("ptxdata_dir_static",))
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
        scenario=scenario, user_data=user_data, data_dir=ptxdata_dir
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


@pytest.mark.parametrize(
    "ptxdata_dir, scenario, kwargs",
    [
        [
            "ptxdata_dir_static",
            "2040 (medium)",
            {
                "source_region_code": "ARE",
                "target_country_code": "DEU",
                "chain_name": "Ammonia (AEL) + reconv. to H2",
                "process_code_res": "PV-FIX",
                "secondary_processes": {"H2O": "DESAL"},
                "ship_own_fuel": False,
                "use_ship": True,
            },
        ],
    ],
)
def test_get_calculation_data(ptxdata_dir, scenario, kwargs, request):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)
    data_handler = DataHandler(data_dir=ptxdata_dir, scenario=scenario)
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
        "context": {"source_region_code": "ARE", "target_country_code": "DEU"},
        "main_process_chain": [
            {
                "EFF": 1,
                "FLH": 1662.0,
                "LIFETIME": 20.0,
                "CAPEX": 689.9185245680053,
                "OPEX-F": 19.317718687904147,
                "OPEX-O": 0,
                "CONV": {},
                "step": "RES",
                "process_code": "PV-FIX",
            },
            {
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "EL_STR",
                "process_code": "EL-STR",
            },
            {
                "EFF": 0.715,
                "FLH": 2779.7,
                "LIFETIME": 20.0,
                "CAPEX": 516.5359022558687,
                "OPEX-F": 10.330718045117374,
                "OPEX-O": 0,
                "CONV": {"H2O-L": 0.3},
                "step": "ELY",
                "process_code": "AEL-EL",
            },
            {
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "H2_STR",
                "process_code": "H2-STR",
            },
            {
                "EFF": 0.819,
                "FLH": 7752.95,
                "LIFETIME": 30.0,
                "CAPEX": 1316.719810985975,
                "OPEX-F": 65.83599054929876,
                "OPEX-O": 0,
                "CONV": {"EL": 0.1419230769230769, "N2-G": 0.1598076923076923},
                "step": "DERIV",
                "process_code": "NH3SYN",
            },
        ],
        "transport_process_chain": [
            {
                "DIST": 12441.9,
                "EFF": 0.9885160879437337,
                "OPEX-T": 3.23721292735082e-07,
                "OPEX-O": 0.00042087134757,
                "CONV": {"BFUEL-L": 5.343656103416341e-06},
                "step": "SHP",
                "process_code": "NH3-SB",
            },
            {
                "EFF": 0.7466101694915254,
                "FLH": 6657.599999999999,
                "LIFETIME": 25.0,
                "CAPEX": 411.4034862565861,
                "OPEX-F": 12.342104587697584,
                "OPEX-O": 0,
                "CONV": {"EL": 0.0076699999999999},
                "step": "POST_SHP",
                "process_code": "NH3-REC",
            },
        ],
        "secondary_process": {
            "H2O": {
                "EFF": 1.0,
                "FLH": 7000,
                "LIFETIME": 20.0,
                "CAPEX": 0.0023667276243093,
                "OPEX-F": 9.466910497237568e-05,
                "OPEX-O": 0,
                "CONV": {"EL": 0.003},
                "process_code": "DESAL",
            }
        },
        "parameter": {
            "WACC": 0.055673211551852,
            "CALOR": 33.33,
            "SPECCOST": {
                "BFUEL-L": 0.0027940534453652,
                "CO2-G": 0.038577660276243,
                "EL": 0.07,
                "H2O-L": 0.0011904639950276,
                "HEAT": 0.05,
                "N2-G": 0.01,
            },
        },
        "flh_opt_process": {},
    }


@pytest.mark.xfail()  # expected data needs to be updated
@pytest.mark.parametrize(
    "ptxdata_dir, scenario, kwargs",
    [
        [
            "ptxdata_dir_static",
            "2040 (medium)",
            {
                "source_region_code": "ARG",
                "target_country_code": "DEU",
                "chain_name": "Ammonia (AEL) + reconv. to H2",
                "process_code_res": "RES-HYBR",
                "secondary_processes": {"H2O": "DESAL"},
                "ship_own_fuel": False,
                "use_ship": True,
            },
        ],
    ],
)
def test_get_calculation_data_w_opt(ptxdata_dir, scenario, kwargs, request):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)

    with TemporaryDirectory() as cache_dir:
        # use temporary dir as cache dir
        data_handler = DataHandler(
            data_dir=ptxdata_dir, scenario=scenario, cache_dir=cache_dir
        )
        result = data_handler.get_calculation_data(**kwargs, optimize_flh=True)
    exp_result = {
        "flh_opt_process": {
            "PV-FIX": {
                "EFF": 1,
                "FLH": 1494.0,
                "LIFETIME": 20.0,
                "CAPEX": 669.3520799156241,
                "OPEX-F": 18.74185823763748,
                "OPEX-O": 0,
                "CONV": {},
            },
            "WIND-ON": {
                "EFF": 1,
                "FLH": 5369.0,
                "LIFETIME": 20.0,
                "CAPEX": 1666.7692273242417,
                "OPEX-F": 46.669538365078765,
                "OPEX-O": 0,
                "CONV": {},
            },
        },
        "main_process_chain": [
            {
                "EFF": 1,
                "FLH": 4200.301925374636,
                "LIFETIME": 20.0,
                "CAPEX": 1666.7692273242417,
                "OPEX-F": 46.669538365078765,
                "OPEX-O": 0.0,
                "CONV": {},
                "step": "RES",
                "process_code": "RES-HYBR",
            },
            {
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "EL_STR",
                "process_code": "EL-STR",
            },
            {
                "EFF": 0.715,
                "FLH": 8759.999999999998,
                "LIFETIME": 20.0,
                "CAPEX": 516.5359022558687,
                "OPEX-F": 10.330718045117374,
                "OPEX-O": 0,
                "CONV": {"H2O-L": 0.3},
                "step": "ELY",
                "process_code": "AEL-EL",
            },
            {
                "EFF": 1,
                "FLH": 7000,
                "LIFETIME": 20,
                "CAPEX": 0,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "H2_STR",
                "process_code": "H2-STR",
            },
            {
                "EFF": 0.819,
                "FLH": 8759.999999999998,
                "LIFETIME": 30.0,
                "CAPEX": 1316.719810985975,
                "OPEX-F": 65.83599054929876,
                "OPEX-O": 0,
                "CONV": {"EL": 0.1419230769230769, "N2-G": 0.1598076923076923},
                "step": "DERIV",
                "process_code": "NH3SYN",
            },
        ],
        "transport_process_chain": [
            {
                "DIST": 12728.796,
                "EFF": 0.9882512820512821,
                "OPEX-T": 3.23721292735082e-07,
                "OPEX-O": 0.00042087134757,
                "CONV": {"BFUEL-L": 5.343656103416341e-06},
                "step": "SHP",
                "process_code": "NH3-SB",
            },
            {
                "EFF": 0.7466101694915254,
                "FLH": 6657.599999999999,
                "LIFETIME": 25.0,
                "CAPEX": 411.4034862565861,
                "OPEX-F": 12.342104587697584,
                "OPEX-O": 0,
                "CONV": {"EL": 0.0076699999999999},
                "step": "POST_SHP",
                "process_code": "NH3-REC",
            },
        ],
        "secondary_process": {
            "H2O": {
                "EFF": 1.0,
                "FLH": 7000,
                "LIFETIME": 20.0,
                "CAPEX": 0.0023667276243093,
                "OPEX-F": 9.466910497237568e-05,
                "OPEX-O": 0,
                "CONV": {"EL": 0.003},
                "process_code": "DESAL",
            }
        },
        "parameter": {
            "WACC": 0.1503103535592313,
            "CALOR": 33.33,
            "SPECCOST": {
                "BFUEL-L": 0.0027940534453652,
                "CO2-G": 0.038577660276243,
                "EL": 0.07,
                "H2O-L": 0.0011904639950276,
                "HEAT": 0.05,
                "N2-G": 0.01,
            },
        },
        "context": {"source_region_code": "ARG", "target_country_code": "DEU"},
    }

    assert_deep_equal(exp_result, result)
