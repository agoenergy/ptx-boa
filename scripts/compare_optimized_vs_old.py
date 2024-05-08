# -*- coding: utf-8 -*-
"""Compare cost results and flh from optimized vs non-optimized FLH."""
import itertools
import json
import logging
import sys
from pathlib import Path
from typing import Literal

import click
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


def main(
    out_file: str | Path,
    cache_dir: Path = DEFAULT_CACHE_DIR,
    transport: Literal["all"] | list = "all",
    ship_own_fuel: Literal["all"] | list = "all",
    secproc_water: Literal["all"] | list = "all",
    secproc_co2: Literal["all"] | list = "all",
    scenario: Literal["all"] | list = "all",
    country: Literal["all"] | list = "all",
    res_gen: Literal["all"] | list = "all",
    region: Literal["all"] | list = "all",
    chain: Literal["all"] | list = "all",
    process_type_filter: None | list = None,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
):
    fmt = "[%(asctime)s %(levelname)7s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(
        level=loglevel.upper(),
        format=fmt,
        datefmt=datefmt,
    )
    out_file = Path(out_file).resolve()
    cache_dir = Path(cache_dir)
    if not cache_dir.exists():
        raise FileNotFoundError(f"cache_dir does not exists {cache_dir}")

    logging.info(f"using cache_dir: {cache_dir}")

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
            if not isinstance(dv, list):
                raise TypeError(f"{dim} must be of type list")
            if not all(x in param_arrays_complete[dim] for x in dv):
                raise ValueError(
                    f"entries of {dim} must be in {param_arrays_complete[dim]}"
                )
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

    n_total = np.prod([len(x) for x in param_arrays.values()])
    logging.warning(f"calculating costs for {n_total} parameter sets")
    optimized_col = "value_optimized"
    no_optimized_col = "value_not_optimized"

    results = []
    for i, param_set in enumerate(product_dict(**param_arrays)):
        if i % 1000 == 0:
            logging.warning(f"{i} of {n_total} parameter combinations")
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

            if process_type_filter is not None:
                df = df.loc[df.index.isin(process_type_filter, level="process_type"), :]

            results.append(df.reset_index())

        except KeyError as e:
            logging.error(f"Not possible to caluclate param_set {param_set}")
            logging.error(f"KeyError: {e}")
            pass

        except AssertionError:
            logging.error("AssertionError: invalid parameter combination")
            pass

    results = pd.concat(results, axis=0, ignore_index=True)
    results.to_csv(
        out_file,
        index=False,
    )
    metadata_file = str(out_file) + "metadata.json"
    metadata = param_arrays | {"process_type_filter": process_type_filter}
    with open(metadata_file, mode="r", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return results


@click.command()
@click.argument(
    "out_file",
    type=click.Path(file_okay=True, dir_okay=False, resolve_path=True, path_type=Path),
)
@click.option(
    "--cache-dir",
    "-c",
    type=click.Path(
        file_okay=False,
        dir_okay=True,
        exists=True,
        readable=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=DEFAULT_CACHE_DIR,
)
@click.option(
    "--loglevel",
    "-l",
    type=click.Choice(["debug", "info", "warning", "error"], case_sensitive=False),
    default="info",
    show_default=True,
)
def cli(out_file: Path, cache_dir: Path, loglevel) -> None:
    if out_file.exists():
        warn_msg = f"out_file exists:{out_file}"
        confirm_msg = "Do you want to continue and overwrite the content in out_file?"
        logging.warning(warn_msg)
        if not click.confirm(
            confirm_msg,
            default=False,
        ):
            logging.info("stopping execution based on user input")
            return None

    main(
        out_file=out_file,
        cache_dir=cache_dir,
        loglevel=loglevel,
        # settings we agreed on which make the results file small and give us
        # relevant results only:
        transport=["Ship"],
        ship_own_fuel=[False],
        secproc_water=["Specific costs"],
        secproc_co2=["Specific costs"],
        scenario="all",
        country=["Germany"],
        res_gen="all",
        region="all",
        chain="all",
        process_type_filter=[
            "Derivate production",
            "Electricity and H2 storage",
            "Electricity generation",
            "Electrolysis",
        ],
    )


if __name__ == "__main__":
    cli()
