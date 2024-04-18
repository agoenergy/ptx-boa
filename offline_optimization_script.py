# -*- coding: utf-8 -*-
"""Offline optimization of parameter combinations."""

import itertools
import logging
from typing import Literal

import numpy as np

from ptxboa.api import PtxboaAPI


def product_dict(**kwargs):
    """Yield the cartesian product of a dictionary of lists.

    https://stackoverflow.com/a/5228294
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))


def main(
    cache_dir: str | None = None,
    dimensions: list[str] | None = None,
    loglevel: Literal["debug", "info", "warning", "error"] = "info",
):
    fmt = "[%(asctime)s %(levelname)7s] %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"
    logging.basicConfig(level=loglevel, format=fmt, datefmt=datefmt)
    api = PtxboaAPI(
        # cache_dir=cache_dir  # FIXME: not implemented yet
    )

    optimization_param_arrays = {
        "region": api.get_dimension("region")["region_name"].tolist(),
        "scenario": api.get_dimension("scenario").index.tolist(),
        "secproc_water": api.get_dimension("secproc_water").index.tolist(),
        "country": api.get_dimension("country").index.tolist(),
        "res_gen": api.get_dimension("res_gen").index.tolist(),
        "secproc_co2": api.get_dimension("secproc_co2").index.tolist(),
        "chain": api.get_dimension("chain").index.tolist(),
    }

    if dimensions is not None:
        assert all(d in optimization_param_arrays.keys() for d in dimensions)
        used_param_arrays = {
            k: v for k, v in optimization_param_arrays.items() if k in dimensions
        }
    else:
        used_param_arrays = optimization_param_arrays.copy()

    n_total = np.prod([len(x) for x in used_param_arrays.values()])
    one_percent = n_total // 100
    assert len(list(product_dict(**used_param_arrays))) == n_total
    for i, param_set in enumerate(product_dict(**used_param_arrays)):
        if i % one_percent == 0:
            p = i / n_total * 100
            print(f"{p:.2f} % of all parameter combinations calculated")
        try:
            api.calculate(transport="Ship", ship_own_fuel=False, **param_set)
        except Exception as e:
            print(f"Error for {param_set}")
            print(e)


if __name__ == "__main__":
    main()
