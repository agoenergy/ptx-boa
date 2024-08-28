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


def check_all_params_defined(provided_options, available_options):
    """Ensure that provided options are in available options."""
    if not all(x in available_options for x in provided_options):
        missing = [x for x in provided_options if x not in available_options]
        msg = (
            f"wrong parameters passed: {missing}\n\n"
            f"available options: {available_options}"
        )
        raise ValueError(msg)


def generate_param_sets(
    api: PtxboaAPI,
    scenarios: list[str] | None,
    regions: list[str] | None,
    chains: list[str] | None,
    secprocs_water: list[str] | None,
    secprocs_co2: list[str] | None,
    res_gens: list[str] | None,
):
    # specify parameter dimensions not relevant for optimization
    # we choose arbritray values for those
    static_params = {"transport": "Ship", "ship_own_fuel": False, "country": "Germany"}

    # these are the parameter dimensions that are relevant for the optimization
    if scenarios is None:
        scenarios = api.get_dimension("scenario").index.tolist()
    else:
        check_all_params_defined(
            scenarios, api.get_dimension("scenario").index.tolist()
        )

    if regions is None:
        regions = api.get_dimension("region")["region_name"].tolist()
    else:
        check_all_params_defined(
            regions, api.get_dimension("region")["region_name"].tolist()
        )

    if chains is None:
        chains = [
            c
            for c in api.get_dimension("chain").index.tolist()
            if not c.endswith("+ reconv. to H2")
        ]
    else:
        check_all_params_defined(chains, api.get_dimension("chain").index.tolist())

    if secprocs_water is None:
        secprocs_water = api.get_dimension("secproc_water").index.tolist()
    else:
        check_all_params_defined(
            secprocs_water, api.get_dimension("secproc_water").index.tolist()
        )

    if secprocs_co2 is None:
        secprocs_co2 = api.get_dimension("secproc_co2").index.tolist()
    else:
        check_all_params_defined(
            secprocs_co2, api.get_dimension("secproc_co2").index.tolist()
        )

    if res_gens is None:
        res_gens = api.get_dimension("res_gen").index.tolist()
    else:
        check_all_params_defined(res_gens, api.get_dimension("res_gen").index.tolist())

    param_sets = []
    for region in regions:
        # only get availabe technologies for this region
        res_gens_region = [x for x in res_gens if x in api.get_res_technologies(region)]
        param_sets += [
            p | static_params | {"region": region}
            for p in product_dict(
                scenario=scenarios,
                chain=chains,
                res_gen=res_gens_region,
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
    scenarios: list[str] | None = None,
    regions: list[str] | None = None,
    chains: list[str] | None = None,
    secprocs_water: list[str] | None = None,
    secprocs_co2: list[str] | None = None,
    res_gens: list[str] | None = None,
):
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(exist_ok=True)

    out_dir = Path(out_dir) if out_dir else cache_dir
    out_dir.mkdir(exist_ok=True)

    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR, cache_dir=cache_dir)

    param_sets = generate_param_sets(
        api,
        scenarios=scenarios,
        regions=regions,
        chains=chains,
        secprocs_water=secprocs_water,
        secprocs_co2=secprocs_co2,
        res_gens=res_gens,
    )

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
        help="starting index for parallel runs",
    )
    parser.add_argument(
        "-t",
        "--index_to",
        type=int,
        help="final index (exlusive) for parallel runs",
    )
    parser.add_argument(
        "-n",
        "--count_only",
        action="store_true",
        help="only print number of parameter variations and quit.",
    )
    parser.add_argument(
        "-scenarios",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )
    parser.add_argument(
        "-regions",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )
    parser.add_argument(
        "-chains",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )
    parser.add_argument(
        "-secprocs_water",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )
    parser.add_argument(
        "-secprocs_co2",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )
    parser.add_argument(
        "-res_gens",
        action="append",
        default=None,
        type=str,
        help=(
            "pass this option multiple times for more than one parameter. "
            "If not passed, all available parameters will be used."
        ),
    )

    args = parser.parse_args()
    main(**vars(args))
