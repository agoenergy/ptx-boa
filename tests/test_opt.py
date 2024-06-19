# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging
from json import load
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pypsa
import pytest

from app.plot_functions import prepare_data_for_profile_figures
from app.tab_optimization import calc_aggregate_statistics
from flh_opt.api_opt import get_profiles_and_weights, optimize
from ptxboa import DEFAULT_CACHE_DIR
from ptxboa.api import DataHandler, PtxboaAPI

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


@pytest.mark.parametrize("chain", ["Methane (AEL)", "Hydrogen (AEL)", "LOHC (AEL)"])
def test_issue_403_fix_no_heat_demand_for_methane_production(api, chain):
    """See https://github.com/agoenergy/ptx-boa/issues/403.

    Heat costs should be zero for Methane and Hydrogen, and >0 for LOHC.
    """
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
    df = res[0]
    if chain != "LOHC (AEL)":
        assert sum(df["process_type"] == "Heat") == 0
    else:
        assert df.loc[df["process_type"] == "Heat", "values"].values[0] > 0


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


def test_prepare_data_for_optimize_incl_sec_proc():
    """Data for optimization should include data for secondary processes."""
    settings = {
        "region": "Morocco",
        "country": "Germany",
        "chain": "Hydrogen (AEL)",
        "res_gen": "PV tilted",
        "scenario": "2040 (medium)",
        "secproc_co2": "Direct Air Capture",  # specified, but will not be used!
        "secproc_water": "Sea Water desalination",
        "transport": "Pipeline",
        "ship_own_fuel": False,
        "user_data": None,
    }
    secondary_processes = {
        "H2O-L": (
            DataHandler.get_dimensions_parameter_code(
                "secproc_water", settings["secproc_water"]
            )
            if settings["secproc_water"]
            else None
        ),
        "CO2-G": (
            DataHandler.get_dimensions_parameter_code(
                "secproc_co2", settings["secproc_co2"]
            )
            if settings["secproc_co2"]
            else None
        ),
    }
    chain_name = settings["chain"]
    process_code_res = DataHandler.get_dimensions_parameter_code(
        "res_gen", settings["res_gen"]
    )
    source_region_code = DataHandler.get_dimensions_parameter_code(
        "region", settings["region"]
    )
    target_country_code = DataHandler.get_dimensions_parameter_code(
        "country", settings["country"]
    )
    use_ship = settings["transport"] == "Ship"
    ship_own_fuel = settings["ship_own_fuel"]

    with TemporaryDirectory() as cache_dir:
        data_handler = DataHandler(
            scenario=settings["scenario"],
            cache_dir=cache_dir,
            data_dir=ptxdata_dir_static,
        )

        # prepare data in the same way as in PtxboaAPI.calculate():
        data = data_handler._get_calculation_data(
            secondary_processes=secondary_processes,
            chain_name=chain_name,
            process_code_res=process_code_res,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_ship=use_ship,
            ship_own_fuel=ship_own_fuel,
            use_user_data=False,
        )

        # prepare data same way as in PtxOpt.get_data()
        opt_input_data = data_handler.optimizer._prepare_data(data)

        # check that some values exist
        assert opt_input_data["H2O"]["CAPEX_A"]
        assert opt_input_data["H2O"]["CONV"]
        assert not opt_input_data.get("CO2")

        opt_metadata, hash_sum = data_handler.optimizer._get_hashsum(
            data, opt_input_data
        )
        assert not opt_metadata["opt_input_data"].get("CO2")
        assert opt_metadata["opt_input_data"].get("H2O")
        # will change if data changes
        assert hash_sum == "15d51a4d030cd561e7a40aa705e35aab"

        # actually call optimizer as in PtxOpt.get_data()
        opt_output_data, _network = optimize(
            opt_input_data,
            profiles_path=data_handler.optimizer.profiles_hashes.profiles_path,
        )

        # check that some values exist
        assert opt_output_data["H2O"]["FLH"]
        assert not opt_output_data.get("CO2")

        # do the same using the proper api call

        data = data_handler.get_calculation_data(
            secondary_processes=secondary_processes,
            chain_name=chain_name,
            process_code_res=process_code_res,
            source_region_code=source_region_code,
            target_country_code=target_country_code,
            use_ship=use_ship,
            ship_own_fuel=ship_own_fuel,
            optimize_flh=True,
            use_user_data_for_optimize_flh=False,
        )


def test_prepare_data_for_profile_figures(call_optimize):
    """Test if solver finds optimal solution."""
    [res, n, input_data] = call_optimize
    print(n)
    df_sel = prepare_data_for_profile_figures(n)

    assert isinstance(df_sel, pd.DataFrame)
    assert len(df_sel) > 0
