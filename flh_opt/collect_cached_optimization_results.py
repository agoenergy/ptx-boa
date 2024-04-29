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
from app.tab_optimization import calc_aggregate_statistics  # noqa E402
from ptxboa import DEFAULT_CACHE_DIR  # noqa E402


def main(
    cache_dir: Path = DEFAULT_CACHE_DIR,
    out_dir: Path = None,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
):
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

    results = []
    network_statistics = []

    filepath_index = out_dir / "offline_optimization.results.json"
    with open(filepath_index, encoding="utf-8") as file:
        index = json.load(file)

    for row in index:
        params = row["params"]
        error = row.get("error")
        if error:
            result = {}
        else:  # no error
            hashinfo = row["result"] if not error else {}
            filepath = Path(hashinfo["filepath"])
            f_hash = hashinfo["hash_md5"]

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
                s = calc_aggregate_statistics(network)
                s["optimization_hash"] = f_hash
                network_statistics.append(s)
            except (FileNotFoundError, ValueError) as e:
                logging.error(f"Error for Network {network_path}: {e}")
                pass

        result["optimization_hash"] = f_hash
        result = result | params

        results.append(result)

    # extract record in "main_process_chain"
    main_process_chain = extract_main_process_chain_data(results)

    secondary_process = extract_secondary_process_data(results)

    logging.info(f"writing collected data to {out_dir}")
    main_process_chain.to_csv(
        out_dir / "cached_optimization_data_main_process_chain.csv"
    )
    secondary_process.to_csv(out_dir / "cached_optimization_data_secondary_process.csv")

    if len(network_statistics) > 0:
        network_statistics = pd.concat(network_statistics)
        network_statistics.to_csv(out_dir / "network_statistics.csv")

    return main_process_chain


def extract_secondary_process_data(results):
    secondary_process = pd.json_normalize(results)
    secondary_process = secondary_process.drop(
        columns=["main_process_chain", "transport_process_chain"]
    )

    return secondary_process


def extract_main_process_chain_data(results):
    df = pd.json_normalize(
        results,
        record_path=["main_process_chain"],
        meta=["context", "optimization_hash", "model_status"],
    )
    # normalize entries in "context" to single columns
    df = pd.concat(
        [
            df.drop(columns="context"),
            pd.json_normalize(df["context"]),
        ],
        axis=1,
    )

    return df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=("Collect optimization data."))
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
        help=("Directory where collected data is written to."),
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
    main(cache_dir=args.cache_dir, out_dir=args.out_dir, loglevel=args.loglevel)
