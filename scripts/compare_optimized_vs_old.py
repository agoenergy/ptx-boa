# -*- coding: utf-8 -*-
"""Compare cost results and flh from optimized vs non-optimized FLH."""
import itertools
import logging
import random
import sys
from pathlib import Path
from typing import Literal

import numpy as np
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))
from ptxboa import DEFAULT_CACHE_DIR, DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI

SERVER_CACHE_DIR = Path("/home/ptxboa/ptx-boa_offline_optimization/optimization_cache")


def product_dict(**kwargs):
    """Yield the cartesian product of a dictionary of lists.

    https://stackoverflow.com/a/5228294
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))


def random_sample(param_arrays):
    return {k: random.choice(v) for k, v in param_arrays.items()}  # noqa S311


def main(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    out_dir: Path = None,
    loglevel: Literal["debug", "info", "warning", "error"] = "warning",
):
    pass


cache_dir = SERVER_CACHE_DIR
out_dir = None
transport = "all"
ship_own_fuel = "all"
secproc_water = "all"
secproc_co2 = "all"
scenario = ["2030 (medium)"]
country = "all"
res_gen = "all"
region = ["Morocco", "Argentina"]
chain = "all"

loglevel = "warning"

fmt = "[%(asctime)s %(levelname)7s] %(message)s"
datefmt = "%Y-%m-%d %H:%M:%S"
logging.basicConfig(
    level=loglevel.upper(),
    format=fmt,
    datefmt=datefmt,
)
cache_dir = Path(cache_dir)
if not cache_dir.exists():
    raise FileNotFoundError(f"cache_dir doe not exists {cache_dir}")

out_dir = Path(out_dir).resolve() if out_dir else cache_dir
out_dir.mkdir(parents=True, exist_ok=True)


api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR, cache_dir=cache_dir)

param_arrays_complete = {
    "transport": api.get_dimension("transport").index.tolist(),
    "ship_own_fuel": [True, False],
    "secproc_water": api.get_dimension("secproc_water").index.tolist(),
    "secproc_co2": api.get_dimension("secproc_co2").index.tolist(),
    "scenario": api.get_dimension("scenario").index.tolist(),
    "country": api.get_dimension("country").index.tolist(),
    "res_gen": api.get_dimension("res_gen").index.tolist(),
    "region": api.get_dimension("region")["region_name"].tolist(),
    "chain": api.get_dimension("chain").index.tolist(),
}
# remove tracking PV (not implemented)
try:
    param_arrays_complete["res_gen"].remove("PV tracking")
except ValueError:
    pass

passed_dims = {
    "transport": transport,
    "ship_own_fuel": ship_own_fuel,
    "secproc_water": secproc_water,
    "secproc_co2": secproc_co2,
    "scenario": scenario,
    "country": country,
    "res_gen": res_gen,
    "region": region,
    "chain": chain,
}

param_arrays = {}
for dim, dv in passed_dims.items():
    if dv == "all":
        param_arrays[dim] = param_arrays_complete[dim]
    else:
        assert isinstance(dv, list)
        assert all(x in param_arrays_complete[dim] for x in dv)
        param_arrays[dim] = dv


index_cols = [
    "process_type",
    "process_subtype",
    "cost_type",
    "scenario",
    "secproc_co2",
    "secproc_water",
    "chain",
    "res_gen",
    "region",
    "country",
    "transport",
]
n_total = len(list(product_dict(**param_arrays)))
logging.info(f"calculating costs for {n_total} parameter sets")
optimized_col = "optimized_flh"
no_optimized_col = "no_optimized_flh"

results = []
for i, param_set in enumerate(product_dict(**param_arrays)):
    if i % 1000 == 0:
        logging.info(f"{i} of {n_total} parameter combinations")
    try:
        df_no_opt = (
            api.calculate(optimize_flh=False, **param_set)[0]
            .rename(columns={"values": no_optimized_col})
            .set_index(index_cols)
        )
        try:
            df_opt = (
                api.calculate(optimize_flh=True, **param_set)[0]
                .rename(columns={"values": optimized_col})
                .set_index(index_cols)
            )
            df = pd.concat(
                [df_no_opt, df_opt],
                axis=1,
            )
        except KeyError as e:
            logging.error(
                f"Not possible to caluclate optimization for param_set {param_set}"
            )
            logging.error(f"KeyError: {e}")
            df = df_no_opt.copy()
            df[optimized_col] = np.nan

        results.append(df.reset_index())

    except KeyError as e:
        logging.error(f"Not possible to caluclate param_set {param_set}")
        logging.error(f"KeyError: {e}")
        pass

    except AssertionError:
        logging.error("AssertionError: invalid parameter combination")
        pass


results = pd.concat(results, axis=0, ignore_index=True)
results.to_csv("/home/j.aschauer/ptxboa_result_comparison/cost_comparison_output.csv")
