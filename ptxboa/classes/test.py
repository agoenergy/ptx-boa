"""Test classes."""

import random
from dataclasses import dataclass

from ptxboa.classes._generated import PtxboaParameters, PtxboaProcesss, PtxboaRegions
from ptxboa.classes.base import PtxboaChain, PtxboaRoute


def get_data(**kwargs):
    return random.random()  # noqa


calor = PtxboaParameters.CALOR(_get_data=get_data)
print(calor)

ng_prod_b = PtxboaProcesss.NG_PROD_B(1, _get_data=get_data)
print(ng_prod_b)


Chain = PtxboaChain._create_subclass(
    "MyChain",
    code="MyChain",
    name="MyChain",
    process_types=[PtxboaProcesss.NG_PROD_B, PtxboaProcesss.ATR_91_B],
    template_class_name="PtxboaChain",
)


chain = Chain(1, _get_data=get_data)
print(chain)

print(PtxboaRoute(from_region=PtxboaRegions.ARE, to_region=PtxboaRegions.DEU))


@dataclass(frozen=True, slots=True)
class P:
    code: str

    def create(self) -> "P2":
        """Create P2."""
        return P2(dtype=self, value=1)


@dataclass(frozen=True, slots=True)
class P2:
    dtype: P
    value: float


p = P(code="ss")
