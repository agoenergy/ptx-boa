"""Class based calculation."""

import argparse
import logging
import re
from dataclasses import dataclass
from typing import Iterable

import coloredlogs
import pandas as pd

from ptxboa import DEFAULT_DATA_DIR, logger
from ptxboa.api import _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
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


def main():
    scenario: ScenarioType = "2040 (medium)"
    permutations = create_permutation_names(create_permutations(scenario=scenario))

    for i, (name, settings) in enumerate(permutations.items()):
        # TODO: skip test chain
        if settings.chain == "Blue Iron (blue)*":
            continue

        if i not in (14, 164):
            continue

        logger.info(f"{i + 1}/{len(permutations)}: {settings} => {name}")

        data_handler = DataHandler(
            scenario=scenario, data_dir=DEFAULT_DATA_DIR, user_data=settings.user_data
        )

        chain_def, _tool_version_color, _optimize_flh = (
            _translate_and_validate_user_settings(
                **settings.__dict__, optimize_flh=False
            )
        )
        chain_process = PtxCalc.get_or_create(chain_def)

        parameter_data = chain_process.get_calculation_data(  # noqa
            data_handler=data_handler,
            source_region_code=_df_region_by_name.at[settings.region, "region_code"],  # type: ignore # noqa
            target_country_code=_df_region_by_name.at[settings.country, "region_code"],  # type: ignore # noqa
        )

        results_api = chain_process.calculate(data=parameter_data)
        logger.info(results_api.df_results_cost)
        logger.info(results_api.df_results_emissions_m_g_co2e)

        results = chain_process._calculate(data=parameter_data)

        edge_values_speccost = {  # noqa
            (p, p_): results["parameter_data"][p]["SPECCOST"][p.main_flow_code_out]  # type: ignore
            for p, p_ in chain_process._graph.edges()
            if p.is_market
        }

        edge_values_flows = {
            (p, p_): results["results_flows"][p].main_flow_out
            for p, p_ in chain_process._graph.edges()
        }

        chain_process.plot(
            file_basename=f"{i:03d}_{name}",
            edge_values=edge_values_flows,  # type: ignore
        )


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
