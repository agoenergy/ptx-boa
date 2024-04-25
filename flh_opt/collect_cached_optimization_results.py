# -*- coding: utf-8 -*-
"""
Collect cached results from the full load hours optimization.

Iterates over cache files and writes two files to outdir:
- "cached_optimization_data_main_process_chain.csv"
- "cached_optimization_data_secondary_process.csv"

"""

import argparse
import logging
import pickle  # noqa S403
import sys
from pathlib import Path
from typing import Literal

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))
from ptxboa import DEFAULT_CACHE_DIR


def main(
    outdir: Path,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
):
    fmt = "[%(asctime)s %(levelname)7s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=loglevel.upper(),
        format=fmt,
        datefmt=datefmt,
    )
    outdir = Path(outdir).resolve()
    outdir.mkdir(parents=True, exist_ok=True)

    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        raise FileNotFoundError(f"cache_dir doe not exists {cache_dir}")

    results = []
    for filepath in cache_dir.rglob("*.pickle"):
        with filepath.open("rb") as file:
            result = pickle.load(file)  # noqa S301
            results.append(result)

    # extract record in "main_process_chain"
    main_process_chain = pd.json_normalize(
        results, record_path=["main_process_chain"], meta="context"
    )
    # normalize entries in "context" to single columns
    main_process_chain = pd.concat(
        [
            main_process_chain.drop(columns="context"),
            pd.json_normalize(main_process_chain["context"]),
        ],
        axis=1,
    )

    secondary_process = pd.json_normalize(results)
    secondary_process = secondary_process.drop(
        columns=["main_process_chain", "transport_process_chain"]
    )

    logging.info(f"writing collected data to {outdir}")
    main_process_chain.to_csv(
        outdir / "cached_optimization_data_main_process_chain.csv"
    )
    secondary_process.to_csv(outdir / "cached_optimization_data_secondary_process.csv")

    return main_process_chain


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Collect optimization data."))
    parser.add_argument(
        "-o",
        "--outdir",
        type=Path,
        default=DEFAULT_CACHE_DIR,
        help=("Directory where collected data is written to."),
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
    main(args.outdir, cache_dir=args.cache_dir, loglevel=args.loglevel)
