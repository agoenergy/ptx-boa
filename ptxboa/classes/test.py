"""Test classes."""

import random
from dataclasses import dataclass

from ptxboa.classes._generated import (
    PtxboaChainTemplates,
    PtxboaProcessTypes,
    PtxboaRegions,
)
from ptxboa.classes.base import (
    PtxboaRegion,
    PtxboaTransportType,
    PtxboaTransportTypes,
)
from ptxboa.classes.extra import (
    PtxboaChainTemplate,
    PtxboaProcessChainType,
    PtxboaProcessType,
    PtxboaSecondaryProcessType,
)


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
    secondary_processes: set[PtxboaSecondaryProcessType]


# create process Chain from settings
def create_chain(settings: Settings) -> PtxboaProcessChainType:

    ptypes_import, ptype_transport, ptype_export = (
        settings.chain.split_export_transport_import()
    )
    # add primary process
    ptypes_import = (settings.initial_process_type,) + ptypes_import
    sec_ptypes_import = {t for t in settings.secondary_processes if t.can_use_in_import}
    sec_ptypes_transport = {
        t for t in settings.secondary_processes if t.can_use_in_transport
    }
    sec_ptypes_export = {t for t in settings.secondary_processes if t.can_use_in_export}

    # TODO: maybe drop pipeline depending on setting?
    # but we still need shipping, even if pipeline is selected (not always applicable)

    # create chain types for each phase
    chain_import = PtxboaProcessChainType(
        code="EXPORT",
        name="Export",
        main_process_types=ptypes_import,
        secondary_process_types=sec_ptypes_import,
    )
    chain_transport = PtxboaProcessChainType(
        code="TRANSPORT",
        name="Transport",
        main_process_types=ptype_transport,
        secondary_process_types=sec_ptypes_transport,
    )
    chain_export = PtxboaProcessChainType(
        code="IMPORT",
        name="Import",
        main_process_types=ptype_export,
        secondary_process_types=sec_ptypes_export,
    )
    chain_total = PtxboaProcessChainType(
        code="CHAIN",
        name="Chain",
        main_process_types=(chain_import, chain_transport, chain_export),
        secondary_process_types=set(),
    )
    return chain_total


def main():

    # user settings
    settings = Settings(
        region_from=PtxboaRegions.DZA,
        region_to=PtxboaRegions.DEU,
        transport_type=PtxboaTransportTypes.SHP,
        initial_process_type=PtxboaProcessTypes.NG_PROD_B,
        chain=PtxboaChainTemplates.STL_S_SMR_52_DRI_EAF_PROD_IN_DEMAND,
        secondary_processes={
            PtxboaProcessTypes.CO2_T_S_B,
            PtxboaProcessTypes.HEATPUMP_B,
            PtxboaProcessTypes.CCGT_CC_B,
        },
    )
    chain_type = create_chain(settings=settings)
    print(chain_type)
    chain = chain_type.create(
        get_data=get_data, main_flow_out=chain_type.main_flow_type_out.create(1)
    )
    print(chain)


main()
