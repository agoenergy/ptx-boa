# -*- coding: utf-8 -*-
"""
Offline optimization of parameter combinations.

Optimization on the server:

login as ptxboa user:

$ ssh ptxboa2

navigate to repository folder and update code:

$ cd ptx-boa_offline_optimization/ptx-boa
$ git pull

go back to offline optimization folder and activate virtualenv:

$ cd ..
$ . .venv/bin/activate

run script with cache dir in offline optimization folder:

$ python ptx-boa/offline_optimization_script.py --cache_dir "./optimization_cache"

"""

import argparse
import itertools
import logging
from pathlib import Path
from typing import Literal

import numpy as np

from ptxboa import DEFAULT_CACHE_DIR, DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI


def product_dict(**kwargs):
    """Yield the cartesian product of a dictionary of lists.

    https://stackoverflow.com/a/5228294
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))


def main(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)

    fmt = "[%(asctime)s %(levelname)7s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=loglevel.upper(),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.FileHandler(cache_dir / "offline_optimization_script.log"),
            logging.StreamHandler(),
        ],
    )
    logging.info(f"starting offline optimization script with cache_dir: {cache_dir}")
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR, cache_dir=cache_dir)

    # these are the parameter dimensions that are relevant for the optimization
    param_arrays = {
        "region": api.get_dimension("region")["region_name"].tolist(),
        "scenario": api.get_dimension("scenario").index.tolist(),
        "secproc_water": api.get_dimension("secproc_water").index.tolist(),
        "res_gen": api.get_dimension("res_gen").index.tolist(),
        "secproc_co2": api.get_dimension("secproc_co2").index.tolist(),
        "chain": api.get_dimension("chain").index.tolist(),
    }

    # specify parameter dimensions not relevant for optimization
    # we choose arbritray values for those
    static_params = {"transport": "Ship", "ship_own_fuel": False, "country": "Germany"}

    n_total = np.prod([len(x) for x in param_arrays.values()])
    logging.info(f"Total number of parameter combinations: {n_total}")
    one_percent = n_total // 100
    assert len(list(product_dict(**param_arrays))) == n_total
    for i, param_set in enumerate(product_dict(**param_arrays)):
        if i % one_percent == 0:
            p = i / n_total * 100
            logging.info(f"{p:.2f} % of all parameter combinations calculated")
        try:
            logging.info(f"calculating parameter set {param_set | static_params}")
            api.calculate(optimize_flh=True, **static_params, **param_set)
        except Exception as e:
            logging.error(f"An error occurred for {param_set}: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=("Offline optimization of parameter combinations.")
    )
    parser.add_argument(
        "-c",
        "--cache_dir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help=(
            "Cache directory. Relative path to the directory from where you are "
            "calling the script or absolute path."
        ),
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level for the console.",
    )

    args = parser.parse_args()
    main(cache_dir=args.cache_dir, loglevel=args.loglevel)
