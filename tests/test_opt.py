# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging
from json import load
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pypsa
import pytest

from app.tab_optimization import calc_aggregate_statistics
from flh_opt.api_opt import get_profiles_and_weights, optimize
from ptxboa import DEFAULT_CACHE_DIR
from ptxboa.api import PtxboaAPI

logging.basicConfig(level=logging.INFO)

ptxdata_dir_static = Path(__file__).parent / "test_data"


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


# import test input data sets from json file:
with open("tests/test_optimize_settings.json", "r") as f:
    api_test_settings = load(f)

# extract ids:
api_test_settings_names = []
for i in api_test_settings:
    api_test_settings_names.append(i["id"])


@pytest.fixture(scope="module", params=api_test_settings, ids=api_test_settings_names)
def call_optimize(request):
    input_data = request.param
    [res, n] = optimize(input_data["input_data"])
    return [res, n, input_data]


def test_optimize_optimal_solution(call_optimize):
    """Test if solver finds optimal solution."""
    [res, n, input_data] = call_optimize
    assert res["model_status"][0] == "ok", "Solver status not OK"
    assert res["model_status"][1] == "optimal", "No optimal solution found"


def test_optimize_export_to_netcdf(call_optimize):
    """Write network to netcdf file."""
    [res, n, input_data] = call_optimize
    with TemporaryDirectory() as export_dir:
        n.export_to_netcdf(f"{export_dir}/{input_data['id']}.nc")


@pytest.mark.xfail()
def test_optimize_expected_objective_value(call_optimize):
    """Test for expected objective value."""
    [res, n, input_data] = call_optimize
    assert n.objective == pytest.approx(input_data["expected_ojective_value"])


@pytest.mark.xfail()
def test_optimize_expected_results(call_optimize):
    """Test if obtained results match expected results."""
    [res, n, input_data] = call_optimize
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
        profiles_path="tests/test_profiles",
    )
    if settings["selection"] is not None:
        assert len(res) == len(settings["selection"])

    pd.testing.assert_series_equal(res.sum(), settings["expected_sum"])
    assert settings["expected_weights_sum"] == pytest.approx(weights["weight"].sum())


@pytest.fixture()
def api():
    return PtxboaAPI(data_dir=ptxdata_dir_static, cache_dir=DEFAULT_CACHE_DIR)


@pytest.mark.parametrize("chain", ["Methane (AEL)", "Hydrogen (AEL)"])
def test_issue_312_fix_fhl_optimization_errors(api, chain):
    """See https://github.com/agoenergy/ptx-boa/issues/312."""
    settings = {
        "region": "Morocco",
        "country": "Germany",
        "chain": chain,
        "res_gen": "PV tilted",
        "scenario": "2040 (medium)",
        "secproc_co2": "Specific costs",
        "secproc_water": "Specific costs",
        "transport": "Pipeline",
        "ship_own_fuel": False,
        "output_unit": "USD/t",
    }
    res = api.calculate(**settings, optimize_flh=True)
    assert len(res) > 0


# expected to fail because of pypsa bug https://github.com/PyPSA/PyPSA/issues/866
@pytest.mark.xfail()
@pytest.mark.filterwarnings("always")
def test_e_cyclic_period_minimal_example():
    n = pypsa.Network()

    levels = [[0, 1], [0, 1, 2]]
    index = pd.MultiIndex.from_product(levels)

    n.set_snapshots(index)
    n.add("Bus", "b0")
    n.add(
        "Store",
        "storage",
        bus="b0",
        e_nom=10,
        e_cyclic_per_period=False,
    )
    n.add("Load", name="load", bus="b0", p_set=[1, 2, 1, 1, 2, 1])
    n.add(
        "Generator",
        name="gen",
        bus="b0",
        p_nom=5,
        marginal_cost=[1, 1, 1, 2, 2, 2],
        p_max_pu=[1, 1, 1, 1, 1, 1],
    )

    n.optimize.create_model()
    res = n.optimize.solve_model(solver_name="highs")
    assert res[1] == "optimal"
    n.statistics()


@pytest.fixture
def network(api) -> pypsa.Network:
    settings = {
        "region": "Morocco",
        "country": "Germany",
        "chain": "Methane (AEL)",
        "res_gen": "PV tilted",
        "scenario": "2040 (medium)",
        "secproc_co2": "Specific costs",
        "secproc_water": "Specific costs",
        "transport": "Pipeline",
        "ship_own_fuel": False,
        "user_data": None,
    }
    n, metadata = api.get_flh_opt_network(**settings)
    assert metadata["model_status"] == ["ok", "optimal"], "Model status not optimal"

    return n


def test_calc_aggregate_statistics(network):
    res = calc_aggregate_statistics(network)
    assert isinstance(res, pd.DataFrame)
