# -*- coding: utf-8 -*-
"""Test flh optimization."""

import logging
from json import load
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pypsa
import pytest

from flh_opt.api_opt import get_profiles_and_weights, optimize
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
    return PtxboaAPI(data_dir=ptxdata_dir_static)


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


@pytest.fixture()
def flh_data_old(api) -> pd.DataFrame:
    """Load old FLH data from csv.

    and prepare them for merging with optimization results.
    """
    filename = "ptxboa/data/flh.csv"
    flh_raw = pd.read_csv(filename, index_col=1)

    # filter processes with optimized flh (only those are relevant for comparison)
    flh_raw = flh_raw[
        flh_raw["process_flh"].isin(
            [
                "AEL-EL",
                "NH3SYN",
                "PEM-EL",
                "SOEC-EL",
                "EFUELSYN",
                "DRI",
                "CH4SYN",
                "CH3OHSYN",
            ]
        )
    ]

    # add long names to old flh data:
    api.get_dimension("res_gen")

    flh = (
        flh_raw.merge(
            api.get_dimension("process")[["process_code", "process_name"]],
            left_on="process_res",
            right_on="process_code",
            how="left",
        )
        .drop("process_code", axis=1)
        .rename({"process_name": "process_name_res"}, axis=1)
    )

    flh = (
        flh.merge(
            api.get_dimension("process")[["process_code", "process_name"]],
            left_on="process_ely",
            right_on="process_code",
            how="left",
        )
        .drop("process_code", axis=1)
        .rename({"process_name": "process_name_ely"}, axis=1)
    )

    flh = (
        flh.merge(
            api.get_dimension("process")[["process_code", "process_name"]],
            left_on="process_deriv",
            right_on="process_code",
            how="left",
        )
        .drop("process_code", axis=1)
        .rename({"process_name": "process_name_deriv"}, axis=1)
    )

    flh["source_region_code"] = flh["key"].str.split(",", n=1).str.get(0)
    flh = flh.rename({"process_flh": "process_code"}, axis=1)
    flh["res_gen"] = flh["process_name_res"]

    return flh


@pytest.fixture()
def flh_data_new(api) -> pd.DataFrame:
    """Load optimization results from csv files.

    and prepare them for comparison with old dataset.
    You need to download them from the server first:

    ````
    scp ptxboa2:/home/ptxboa/ptx-boa_offline_optimization/optimization_cache/*.csv .
    ````
    """
    filename_new_data_main = (
        "optimization_results/cached_optimization_data_main_process_chain.csv"
    )
    filename_new_data_secondary = (
        "optimization_results/cached_optimization_data_secondary_process.csv"
    )
    # TODO merge network data as well: "optimization_results/network_statistics.csv"

    flh_new_main = pd.read_csv(filename_new_data_main)
    flh_new_secondary = pd.read_csv(filename_new_data_secondary)

    # merge chain info to new flh data:
    flh_all = pd.merge(
        flh_new_main,
        flh_new_secondary[["optimization_hash", "chain", "res_gen", "scenario"]],
        on="optimization_hash",
        how="left",
    )

    chain_info = api.get_dimension("chain")[["chain", "ELY", "DERIV"]].rename(
        {"ELY": "process_ely", "DERIV": "process_deriv"}, axis=1
    )

    flh_all = flh_all.merge(chain_info, on="chain", how="left")

    # filter for processes that are relevant for comparison:
    flh_all = flh_all[
        flh_all["process_code"].isin(
            [
                "AEL-EL",
                "NH3SYN",
                "PEM-EL",
                "SOEC-EL",
                "EFUELSYN",
                "DRI",
                "CH4SYN",
                "CH3OHSYN",
            ]
        )
    ]

    return flh_all


def get_flh_old(
    flh_data_old: pd.DataFrame,
    process_code: str,
    source_region_code: str,
    process_res: str,
    process_ely: str,
    process_deriv: str,
) -> float:
    """Get scalar flh data point from old dataset."""
    ind1 = flh_data_old["source_region_code"] == source_region_code
    ind2 = flh_data_old["process_code"] == process_code
    ind3 = flh_data_old["process_ely"] == process_ely
    ind3 = flh_data_old["process_res"] == process_res
    ind4 = flh_data_old["process_deriv"] == process_deriv
    res = flh_data_old[ind1 & ind2 & ind3 & ind4]
    return res["value"].values[0]


def test_flh_import(flh_data_old, flh_data_new):
    """Merge new and old flh dataset."""
    merged_data = flh_data_new.merge(
        flh_data_old,
        on=[
            "source_region_code",
            "process_code",
            "process_ely",
            "process_deriv",
            "res_gen",
        ],
        how="left",
    )[
        [
            "FLH",
            "value",
            "process_code",
            "source_region_code",
            "res_gen",
            "scenario",
            "process_ely",
            "process_deriv",
            "process_res",
            "chain",
            "model_status",
        ]
    ]

    merged_data = merged_data.rename(
        {"FLH": "flh_optimized", "value": "flh_old"}, axis=1
    )

    # export merged data to csv:
    merged_data.to_csv("tests/merged_flh_data.csv")

    # test extraction of scalar data point:
    res = get_flh_old(
        flh_data_old,
        source_region_code="MAR",
        process_code="AEL-EL",
        process_res="PV-FIX",
        process_ely="AEL-EL",
        process_deriv="CH3OHSYN",
    )
    assert res == 2771.15
