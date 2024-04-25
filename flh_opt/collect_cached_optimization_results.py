# -*- coding: utf-8 -*-
"""
Collect cached results from the full load hours optimization.

Iterates over cache files and writes two files to outdir:
- "cached_optimization_data_main_process_chain.csv"
- "cached_optimization_data_secondary_process.csv"

"""

import argparse
import json
import logging
import pickle  # noqa S403
import sys
from pathlib import Path
from typing import Literal

import pandas as pd
import pypsa

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
    network_statistics = []
    for filepath in cache_dir.rglob("*.pickle"):
        f_hash = f"{filepath.parents[1].name}{filepath.parent.name}{filepath.stem}"
        # this is the respective network object filepath
        network_path = filepath.parent / f"{filepath.name}.network.nc"
        # this is the metadata filepath
        metadata_path = filepath.parent / f"{filepath.name}.metadata.json"
        with filepath.open("rb") as pfile:
            result = pickle.load(pfile)  # noqa S301

        try:
            with metadata_path.open("r", encoding="utf-8") as mfile:
                metadata = json.load(mfile)
            result["model_status"] = metadata["model_status"]
        except FileNotFoundError:
            result["model_status"] = "NaN"

        try:
            network = pypsa.Network()
            network.import_from_netcdf(network_path)
            network_statistics.append(network.statistics())
        except (FileNotFoundError, ValueError) as e:
            logging.error(f"Error for Network {network_path}: {e}")
            pass

        result["optimization_hash"] = f_hash

        results.append(result)

    # extract record in "main_process_chain"
    main_process_chain = pd.json_normalize(
        results,
        record_path=["main_process_chain"],
        meta=["context", "optimization_hash", "model_status"],
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

    if len(network_statistics) > 0:
        network_statistics = pd.concat(network_statistics)
        network_statistics.to_csv(outdir / "network_statistics.csv")

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
