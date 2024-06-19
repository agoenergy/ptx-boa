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
import json
import logging
import os
from pathlib import Path
from typing import Literal

# don't use tqdm, because we want to suppress
# tqdm bars of optimization process (from linopy)
import progress.bar

# suppress most of the solver output from
# linopy and HIGHs
# (I cant get rid of the Copyright print from HIGHs)
# MUST be set before importing ptxboa
os.environ["HIGHS_OUTPUT_FLAG"] = "false"
os.environ["TQDM_DISABLE"] = "1"


from ptxboa import (  # noqa E402 module level import not at top
    DEFAULT_CACHE_DIR,
    DEFAULT_DATA_DIR,
)
from ptxboa.api import PtxboaAPI  # noqa E402 module level import not at top


def product_dict(**kwargs):
    """Yield the cartesian product of a dictionary of lists.

    https://stackoverflow.com/a/5228294
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))


def generate_param_sets(api: PtxboaAPI):

    # specify parameter dimensions not relevant for optimization
    # we choose arbritray values for those
    static_params = {"transport": "Ship", "ship_own_fuel": False, "country": "Germany"}

    # these are the parameter dimensions that are relevant for the optimization
    scenarios = api.get_dimension("scenario").index.tolist()
    regions = api.get_dimension("region")["region_name"].tolist()
    chains = [
        c
        for c in api.get_dimension("chain").index.tolist()
        if not c.endswith("+ reconv. to H2")
    ]
    secprocs_water = ["Specific costs", "Sea Water desalination"]
    secprocs_co2 = ["Specific costs", "Direct Air Capture"]

    param_sets = []
    for region in regions:
        # only get availabe technologies for this region
        res_gens = api.get_res_technologies(region)
        param_sets += [
            p | static_params | {"region": region}
            for p in product_dict(
                scenario=scenarios,
                chain=chains,
                res_gen=res_gens,
                secproc_water=secprocs_water,
                secproc_co2=secprocs_co2,
            )
        ]

    return param_sets


def main(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    out_dir=None,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
    index_from: int = None,
    index_to: int = None,
    count_only: bool = False,
):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)

    out_dir = Path(out_dir) if out_dir else cache_dir
    out_dir.mkdir(exist_ok=True)

    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR, cache_dir=cache_dir)

    param_sets = generate_param_sets(api)

    if count_only:
        print(f"Number of parameter variations: {len(param_sets)}")
        return

    # filter for batch
    index_from = index_from or 0
    index_to = index_to or len(param_sets)
    param_sets = param_sets[index_from:index_to]

    # set up logging
    fmt = "[%(asctime)s %(levelname)7s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=loglevel.upper(),
        format=fmt,
        datefmt=datefmt,
        handlers=[
            logging.FileHandler(
                cache_dir / f"offline_optimization_script.{index_from}-{index_to}.log"
            ),
        ],
    )
    logging.info(f"starting offline optimization script with cache_dir: {cache_dir}")

    results = []  # save results
    for params in progress.bar.Bar(
        suffix=(
            "%(index)s/%(max)s, "
            "%(percent)d%%, "
            "elapsed %(elapsed_td)s, "
            "eta %(eta_td)s"
        )
    ).iter(param_sets):
        result = {"params": params}
        try:
            logging.info(f"calculating parameter set {params}")

            _df, metadata = api.calculate(optimize_flh=True, **params)

            result["error"] = None
            result["result"] = metadata.get("flh_opt_hash")
        except Exception as e:
            logging.error(f"An error occurred for {params}: {e}")
            result["error"] = str(e)
            result["result"] = None

        results.append(result)

    # save result
    with open(
        out_dir / f"offline_optimization.results.{index_from}-{index_to}.json",
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            results,
            file,
            indent=2,
            ensure_ascii=False,
        )


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
        "-o",
        "--out_dir",
        type=Path,
        default=None,
        help=("Output directory for inupt/output(hashsums)"),
    )
    parser.add_argument(
        "-l",
        "--loglevel",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level for the console.",
    )
    parser.add_argument(
        "-f",
        "--index_from",
        type=int,
        help="starting index for prallel runs",
    )
    parser.add_argument(
        "-t",
        "--index_to",
        type=int,
        help="final index (exlusive) for prallel runs",
    )
    parser.add_argument(
        "-n",
        "--count_only",
        action="store_true",
        help="only print number of parameter variations and quit.",
    )

    args = parser.parse_args()
    main(**vars(args))
