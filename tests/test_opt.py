# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging
import os
from json import dump, load
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Tuple

import pandas as pd
import pypsa
import pytest

from app.plot_functions import prepare_data_for_profile_figures
from app.tab_optimization import calc_aggregate_statistics
from flh_opt.api_opt import get_profiles_and_weights, optimize
from ptxboa import DEFAULT_CACHE_DIR
from ptxboa.api import DataHandler, PtxboaAPI
from ptxboa.utils import annuity

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


@pytest.fixture
def network_green_iron(api) -> Tuple[pypsa.Network, dict, dict]:
    settings = {
        "region": "Morocco",
        "country": "Germany",
        "chain": "Green Iron (AEL)",
        "res_gen": "Wind-PV-Hybrid",
        "scenario": "2040 (medium)",
        "secproc_co2": "Specific costs",
        "secproc_water": "Specific costs",
        "transport": "Pipeline",
        "ship_own_fuel": False,
        "user_data": None,
    }
    n, metadata = api.get_flh_opt_network(**settings)
    assert metadata["model_status"] == ["ok", "optimal"], "Model status not optimal"

    return n, metadata, settings


def test_issue_564(network_green_iron, api):
    # calculate costs from optimization tab:
    n, metadata, settings = network_green_iron
    res_opt = calc_aggregate_statistics(n, include_debugging_output=True)

    # get costs from costs tab:
    df_res_costs, _ = api.calculate(**settings)

    res_costs_agg = df_res_costs.pivot_table(
        index="process_type", columns="cost_type", values="values", aggfunc=sum
    ).fillna(0)

    res_costs_agg["total"] = res_costs_agg.sum(axis=1)
    res_costs_agg.loc["Total"] = res_costs_agg.sum(axis=0)

    # combine both sources to single df:
    res_costs_agg.at["Electricity generation", "total_opt"] = (
        res_opt.at["PV tilted", "Cost (USD/MWh)"]
        + res_opt.at["Wind onshore", "Cost (USD/MWh)"]
    )

    res_costs_agg.at["Derivative production", "total_opt"] = res_opt.at[
        "Derivative production", "Cost (USD/MWh)"
    ]

    res_costs_agg.at["Electricity and H2 storage", "total_opt"] = (
        res_opt.at["H2 storage", "Cost (USD/MWh)"]
        + res_opt.at["Electricity storage", "Cost (USD/MWh)"]
    )

    res_costs_agg.at["Electrolysis", "total_opt"] = res_opt.at[
        "Electrolyzer", "Cost (USD/MWh)"
    ]

    res_costs_agg.at["Water", "total_opt"] = res_opt.at[
        "Water supply", "Cost (USD/MWh)"
    ]

    res_costs_agg["diff"] = (
        res_costs_agg["total_opt"] - res_costs_agg["total"]
    ).fillna(0)

    # call optimize function directly:
    res_optimize = optimize(metadata["opt_input_data"])[0]

    # write costs data to excel, and metadata to json:
    if not os.path.exists("tests/out"):
        os.makedirs("tests/out")
    res_costs_agg.to_excel("tests/out/test_issue_564.xlsx")
    with open("tests/out/issue_564_metadata_optimize_input.json", "w") as f:
        dump(metadata, f)
    with open("tests/out/issue_564_metadata_optimize_output.json", "w") as f:
        dump(res_optimize, f)

    # extract DRI input data:
    input_data = api.get_input_data(scenario=settings["scenario"])
    input_data_dri = input_data.loc[
        input_data["process_code"] == "Green iron reduction"
    ].set_index("parameter_code")
    wacc = input_data.loc[
        (input_data["parameter_code"] == "WACC")
        & (input_data["source_region_code"] == settings["region"]),
        "value",
    ].values[0]
    capex = input_data_dri.at["CAPEX", "value"]
    periods = input_data_dri.at["lifetime / amortization period", "value"]
    opex_fix = input_data_dri.at["OPEX (fix)", "value"]

    capex_ann_input = annuity(wacc, periods, capex)
    capex_ann_opt = res_opt.at["Derivative production", "CAPEX (USD/kW)"]

    # annuized capex should match:
    assert capex_ann_input + opex_fix == pytest.approx(capex_ann_opt)

    # FLH from optimization tab and optimize function output should match:
    flh_opt_tab = res_opt.at["Derivative production", "Full load hours (h)"]
    flh_opt_function = res_optimize["DERIV"]["FLH"] * 8760
    assert flh_opt_tab == pytest.approx(flh_opt_function)

    # assert that differences between costs and opt tab are zero:
    # this currently fails
    for i in res_costs_agg["diff"]:
        assert i == pytest.isclose(0)


def test_fix_green_iron(network_green_iron):
    """Test optimize input data: CAPEX of electricity storage should not be zero.

    See https://github.com/agoenergy/ptx-boa/issues/554
    """
    n, metadata, settings = network_green_iron
    assert metadata["opt_input_data"]["EL_STR"]["CAPEX_A"] != 0


def test_output_of_final_product_is_8760mwh(network_green_iron):
    """Test that output of final process step is 8760MWh/a."""
    n, metadata, settings = network_green_iron
    res = calc_aggregate_statistics(n)

    assert res.at["Derivative production", "Output (MWh/a)"] == pytest.approx(8760)


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
        assert hash_sum == "372bfe666946ac49f751d0656a670421"

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
