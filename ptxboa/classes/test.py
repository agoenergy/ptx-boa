"""Test classes."""

import random

from ptxboa.classes._generated import (
    PtxboaFlowTypes,
    PtxboaParameterTypes,
    PtxboaProcessTypes,
    PtxboaRegions,
)
from ptxboa.classes.base import PtxboaRoute
from ptxboa.classes.extra import PtxboaProcessTreeType


def get_data(**_kwargs):
    return random.random()  # noqa


eff = PtxboaParameterTypes.EFF.create(get_data=get_data)
route = PtxboaRoute(from_region=PtxboaRegions.ARE, to_region=PtxboaRegions.DEU)
h2 = PtxboaFlowTypes.H2_G.create(value=1)
ngp = PtxboaProcessTypes.NG_PROD_B.create(
    get_data=get_data, main_flow_out=PtxboaFlowTypes.NG_G.create(1)
)

dac = PtxboaProcessTypes.DAC_B.create(
    get_data=get_data, main_flow_out=PtxboaFlowTypes.CO2_G.create(1)
)

print(PtxboaRegions.DEU)
print(route)
print(PtxboaParameterTypes.EFF)
print(eff)
print(PtxboaFlowTypes.H2_G)
print(h2)
print(PtxboaProcessTypes.NG_PROD_B)
print(ngp)
print(dac)


tree_type = PtxboaProcessTreeType(
    code="my_chain",
    name="my_chain",
    process_types=(
        PtxboaProcessTypes.NG_PROD_B,
        PtxboaProcessTypes.ATR_91_B,
    ),
    secondary_flows=(),
)
print(tree_type)

tree = tree_type.create(get_data=get_data, main_flow_out=PtxboaFlowTypes.H2_G.create(1))

print(tree)
