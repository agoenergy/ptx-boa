"""Test classes."""

import random
from dataclasses import dataclass

from ptxboa.classes._generated import (
    PtxboaChainTemplates,
    PtxboaProcessTypes,
    PtxboaRegions,
    PtxboaSecondaryProcessType,
)
from ptxboa.classes.base import (
    PtxboaChainTemplate,
    PtxboaRegion,
    PtxboaTransportType,
    PtxboaTransportTypes,
)
from ptxboa.classes.extra import PtxboaProcessChainType, PtxboaProcessType


def get_data(**_kwargs):
    return random.random()  # noqa


@dataclass(frozen=True, slots=True)
class Settings:
    region_from: PtxboaRegion
    region_to: PtxboaRegion
    transport_type: PtxboaTransportType
    initial_process_type: (
        PtxboaProcessType  # TODO: restrict to RES/NG_PROD for green/blue
    )
    chain: PtxboaChainTemplate
    secondary_processes: tuple[PtxboaSecondaryProcessType, ...]


# user settings
settings = Settings(
    region_from=PtxboaRegions.DZA,
    region_to=PtxboaRegions.DEU,
    transport_type=PtxboaTransportTypes.SHP,
    initial_process_type=PtxboaProcessTypes.NG_PROD_B,
    chain=PtxboaChainTemplates.STL_S_SMR_52_DRI_EAF_PROD_IN_DEMAND,
    secondary_processes=(),
)


# create process Chain from settings
def create_chain(settings: Settings) -> PtxboaProcessChainType:
    pass
