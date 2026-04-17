"""Class based calculation."""

import argparse
import logging
import re
from dataclasses import dataclass
from typing import Iterable

import coloredlogs
import pandas as pd

from ptxboa import DEFAULT_DATA_DIR, logger
from ptxboa.api import PtxboaAPI, PtxCalc
from ptxboa.api_data import DataHandler
from ptxboa.static import (
    ChainType,
    ResGenType,
    ScenarioType,
    SecProcCO2Type,
    SecProcH2OType,
    SourceRegionNameType,
    TargetCountryNameType,
    ToolVersionColorType,
    TransportType,
)

_df_process_by_code = DataHandler.get_dimension("process")
_df_chain = DataHandler.get_dimension("chain")
_df_region_by_name = DataHandler.get_dimension("region")
_df_region_by_code = _df_region_by_name.set_index("region_code", drop=False)

PLOT_TYPES = ["flows", "speccost", "cbound_m", "cbound_e"]


@dataclass
class Settings:
    scenario: ScenarioType
    secproc_co2: SecProcCO2Type | None
    secproc_water: SecProcH2OType | None
    chain: ChainType
    res_gen: ResGenType | None
    region: SourceRegionNameType
    country: TargetCountryNameType
    transport: TransportType
    ship_own_fuel: bool
    user_data: pd.DataFrame | None
    tool_version_color: ToolVersionColorType


def create_permutation_names(permutations: Iterable[Settings]) -> dict[str, Settings]:
    def create_name(settings: Settings) -> str:
        name = (
            f"{settings.chain}_{settings.transport}"
            f"{'_OWN' if settings.ship_own_fuel else ''}"
        )
        name = re.sub("[^A-Za-z0-9-%()]", "_", name)
        return name

    result: dict[str, Settings] = {}
    for settings in permutations:
        name = create_name(settings)
        if name in result:
            raise KeyError(name)
        result[name] = settings
    return result


def create_permutations(scenario: ScenarioType) -> Iterable[Settings]:

    res_gen: ResGenType | None = _df_process_by_code.loc["RES-HYBR", "process_name"]  # type: ignore # noqa
    region: SourceRegionNameType = _df_region_by_code.loc["DZA", "region_name"]  # type: ignore # noqa
    country: TargetCountryNameType = _df_region_by_code.loc["DEU", "region_name"]  # type: ignore # noqagp
    transports: list[tuple[TransportType, bool]] = [
        ("Pipeline", False),
        ("Ship", False),
        ("Ship", True),
    ]

    for chain_spec in _df_chain.to_dict(orient="records"):
        chain = chain_spec["chain"]
        tool_version_color = DataHandler.get_chain_color(chain)
        secproc_co2: SecProcCO2Type | None = (
            "Direct Air Capture (blue)"
            if tool_version_color == "blue"
            else "Direct Air Capture"
        )
        secproc_water: SecProcH2OType | None = "Sea Water desalination"

        for transport, ship_own_fuel in transports:
            if transport == "Pipeline" and not chain_spec["can_pipeline"]:
                continue
            if transport == "Ship" and ship_own_fuel and not chain_spec["SHP_OWN"]:
                continue
            yield Settings(
                scenario=scenario,
                country=country,
                region=region,
                chain=chain,
                ship_own_fuel=ship_own_fuel,
                transport=transport,
                res_gen=res_gen,
                user_data=None,
                tool_version_color=tool_version_color,
                secproc_co2=secproc_co2,
                secproc_water=secproc_water,
            )


def main(chains: list[str], plot_type: str):
    scenario: ScenarioType = "2040 (medium)"
    permutations = create_permutation_names(create_permutations(scenario=scenario))

    for i, (name, settings) in enumerate(permutations.items()):
        # TODO: skip test chain
        if settings.chain == "Blue Iron (blue)*":
            continue

        if chains:
            # only do that
            if settings.chain not in chains:
                continue

        logger.info(f"{i + 1}/{len(permutations)}: {settings} => {name}")

        api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
        output_unit = "USD/t"  # works always
        results = (
            api.calculate(
                **settings.__dict__, output_unit=output_unit, optimize_flh=False
            )._internal_data
            or {}
        )
        chain: PtxCalc = results["chain"]
        graph = chain._graph
        results_flows = results["results_flows"]
        results_emissions = results["results_emissions"]
        parameter_data = results["parameter_data"]

        if plot_type == "flows":
            edge_values = {
                (p, p_): results_flows[p].main_flow_out for p, p_ in graph.edges()
            }
        elif plot_type == "speccost":
            edge_values = {  # noqa
                (p, p_): parameter_data[p]["SPECCOST"][p.main_flow_code_out]  # type: ignore  # noqa
                for p, p_ in graph.edges()
                if p.is_market
            }
        elif plot_type in ("cbound_m", "cbound_e"):
            edge_values = {}
            me = {"cbound_m": "mass", "cbound_e": "emission"}[plot_type]
            for p in graph.nodes():
                res = results_emissions.get(p)
                if not res:
                    continue

                cbound_rel = res[me].co2_bound_in_product_per_output
                cbound_abs = res[me].co2_bound_in_product
                cbound_rel = cbound_abs / results_flows[p].main_flow_out

                if not cbound_rel:
                    continue
                for p_ in p._links_out_in_main:
                    edge_values[(p, p_)] = results_flows[p_].main_flow_in * cbound_rel
                for p_ in p._links_out_in_secondary:
                    edge_values[(p, p_)] = (
                        results_flows[p_].secondary_flows_in[p.main_flow_code_out]
                        * cbound_rel
                    )

        else:
            raise NotImplementedError(plot_type)

        chain.plot(
            file_basename=f"{settings.tool_version_color}/{name}_{plot_type}",
            edge_values=edge_values,  # type: ignore
        )


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loglevel",
        "-l",
        choices=["debug", "info", "warning", "error"],
        default="warning",
    )
    ap.add_argument("chains", nargs="?")
    ap.add_argument("--plot-type", choices=PLOT_TYPES, default=PLOT_TYPES[0])
    # parse args
    kwargs = vars(ap.parse_args())
    # logging
    coloredlogs.install(
        logger=logger,
        level=getattr(logging, kwargs.pop("loglevel").upper()),
        fmt="[%(asctime)s %(levelname)7s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        field_styles={
            "asctime": {"color": "white"},
            "levelname": {"color": "white"},
        },
        level_styles={
            "debug": {"color": "blue"},
            "info": {"color": "green"},
            "warning": {"color": "yellow"},
            "error": {"color": "red"},
        },
    )

    main(**kwargs)
