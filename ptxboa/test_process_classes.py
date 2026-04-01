"""Class based calculation."""

import argparse
import logging
import re
from dataclasses import dataclass
from typing import Iterable, cast

import coloredlogs
import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

from ptxboa import logger
from ptxboa.api_data import DataHandler
from ptxboa.process_classes import (
    AbstractProcess,
    AggregateProcess,
    MarketProcess,
    Process,
    create_chain_process_api_wrapper,
)
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
        tool_version_color: ToolVersionColorType = (
            "green" if chain_spec["is_green"] else "blue"
        )
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


def plot_get_pos(
    chain_process: AggregateProcess,
) -> dict[AbstractProcess, tuple[float, float]]:

    node_pos = {}
    xs: list[float] = [0, 0, 0]
    proc_end_last = None

    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        xs[1] = max(xs[0] + 0.25, xs[0])  # stagger
        xs[2] = max(xs[0], xs[2])

        sgn = 1  # secondary process: offset sign should alternate between -1 and 1

        for process in reversed(list(process_graph.calculate_order)):
            key = process

            # if is_main:
            if process in process_graph.main_processes:
                xs[0] = xs[0] + 2
                x = xs[0]
                y = 0
                if not proc_end_last and process == process_graph.main_processes[0]:
                    y = 0.05  # initial a little closer to secondary
            elif not isinstance(process, MarketProcess):
                #  is secondary
                xs[1] = xs[1] + 1.5
                x = xs[1]
                # non linear disntance for non overlapping arrows
                y = 0.1 + 0.008 * sgn
                sgn = -sgn  # alterante
            else:
                # market
                xs[2] = xs[2] + 1
                x = xs[2]
                y = 0.2

            node_pos[key] = (x, y)

        proc_end_last = process_graph.main_processes[-1]

    return node_pos


def nested_round_drop_empty(x):
    if isinstance(x, list):
        return [nested_round_drop_empty(v) for v in x]
    elif isinstance(x, dict):
        result = {k: nested_round_drop_empty(v) for k, v in x.items()}
        result = {k: v for k, v in result.items() if v}
        return result
    elif isinstance(x, float):
        return round(x, 4)
    else:
        return x


def plot(chain_process: AggregateProcess, name: str):

    # Create a directed graph
    G = nx.DiGraph()
    node_labels = {}
    edge_labels = {}
    edge_widths = {}

    proc_end_last = None
    len_main_total = 0
    for ex_tr_imp in chain_process.process_graph.main_processes:
        ex_tr_imp = cast(AggregateProcess, ex_tr_imp)
        # export / tranport / import  subgraph

        process_graph = ex_tr_imp.process_graph

        # add processes as nodes to DiGraph

        for process in reversed(list(process_graph.calculate_order)):
            label = str(process)

            G.add_node(process)
            node_labels[process] = (
                label.replace("=", "\n")
                .replace("(", "\n")
                .replace(")", "\n")
                .replace(" ", "\n")
                .strip()
            )

            for proc_target, in_main in process_graph.links_out.get(process, []):
                flow = process.main_flow_code_out
                e = (process, proc_target)
                G.add_edge(*e)
                try:
                    value = (
                        proc_target.get_main_flow_in()
                        if in_main
                        else proc_target.get_secondary_flow_in(flow)
                    )
                    value_str = f"\n{value:.4f}"
                except Exception:
                    value_str = ""
                edge_labels[e] = f"{flow}{value_str}"
                edge_widths[e] = 2 if in_main else 1

        if proc_end_last:
            # link from previous subpgraph
            proc_start = process_graph.main_processes[0]
            e = (proc_end_last, proc_start)
            G.add_edge(*e)
            edge_labels[e] = proc_end_last.main_flow_code_out
            try:
                edge_labels[e] += f"\n{proc_start.get_main_flow_in():.4f}"
            except Exception:  # not calculated yet, # noqa: S110
                pass
            edge_widths[e] = 2

        proc_end_last = process_graph.main_processes[-1]

        len_main_total += len(process_graph.main_processes)

    scale = 3

    # node_pos = nx.circular_layout(G) # noqa
    node_pos = plot_get_pos(chain_process=chain_process)

    plt.close()
    plt.clf()
    plt.figure(figsize=(len_main_total * scale, 2 * scale))

    # Draw nodes
    nx.draw(
        G,
        node_pos,
        with_labels=False,
        node_color=[cast(Process, k).color for k in G.nodes()],
        width=[edge_widths[k] for k in G.edges()],
        node_size=2000 * scale,
    )

    # Draw node labels
    nx.draw_networkx_labels(
        G, node_pos, labels=node_labels, font_size=6, font_color="black"
    )

    # Draw edge labels
    nx.draw_networkx_edge_labels(
        G,
        node_pos,
        edge_labels=edge_labels,
        font_size=6,
        font_color="black",
        # label_pos=0.5, # noqa
    )

    # Save to PNG
    plt.savefig(f"chain_flowcharts/{name}.png", dpi=300)


def main():
    scenario: ScenarioType = "2040 (medium)"
    permutations = create_permutation_names(create_permutations(scenario=scenario))

    for i, (name, settings) in enumerate(permutations.items()):
        if name == "STL-S__NG-DRI-C_EAF__prod_in_supply_Ship":
            # test 1
            settings.region = "Qatar"
        elif name == "STL-S__NG-DRI-C_EAF__prod_in_demand_Ship":
            pass
        else:
            continue
            pass

        logger.info(f"{i + 1}/{len(permutations)}: {settings} => {name}")

        chain_process = create_chain_process_api_wrapper(**settings.__dict__)

        plot(chain_process, name=name)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--loglevel",
        "-l",
        choices=["debug", "info", "warning", "error"],
        default="warning",
    )
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
