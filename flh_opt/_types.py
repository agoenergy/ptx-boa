# -*- coding: utf-8 -*-
"""Type definitions."""

import json
import random
import string
from typing import Dict, List, Literal, TypedDict, get_args, get_origin

ProcessCodeResType = Literal["PV-FIX", "PV-TRK", "RES-HYBR", "WIND-OFF", "WIND-ON"]
ProcessCodeDerivType = Literal["CH3OHSYN", "CH4SYN", "DRI", "EFUELSYN", "NH3SYN"]
SecondaryFlowType = Literal[
    "BFUEL-L",
    "CH3OH-L",
    "CH4-G",
    "CH4-L",
    "CHX-L",
    "CO2-G",
    "C-S",
    "DRI-S",
    "EL",
    "H2-G",
    "H2-L",
    "H2O-L",
    "HEAT",
    "LOHC-L",
    "N2-G",
    "NH3-L",
]


class ProcessElyInputDataType(TypedDict):
    EFF: float
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float
    CONV: Dict[Literal["H2O-L"], float]


class ProcessStorageInputDataType(TypedDict):
    EFF: float
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float


class ProcessResInputDataType(TypedDict):
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float
    PROCESS_CODE: ProcessCodeResType


class ProcessDerivInputData(TypedDict):
    EFF: float
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float
    PROCESS_CODE: ProcessCodeDerivType
    CONV: Dict[SecondaryFlowType, float]


class SecProcessInputDataType(TypedDict):
    # EFF: Does not use EFF parameter
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float
    CONV: Dict[SecondaryFlowType, float]


class OptInputDataType(TypedDict):
    SOURCE_REGION_CODE: str
    RES: List[ProcessResInputDataType]
    ELY: ProcessElyInputDataType
    DERIV: ProcessDerivInputData
    EL_STR: ProcessStorageInputDataType
    H2_STR: ProcessStorageInputDataType
    SPECCOST: Dict[Literal["H2O-L"], float]
    CO2: SecProcessInputDataType
    H2O: SecProcessInputDataType


class ProcessOutputResType(TypedDict):
    SHARE_FACTOR: float
    FLH: float
    PROCESS_CODE: ProcessCodeResType


class OptOutputDataType(TypedDict):
    RES: List[ProcessOutputResType]
    ELY: Dict[Literal["FLH"], float]
    DERIV: Dict[Literal["FLH"], float]
    CO2: Dict[Literal["FLH"], float]
    H2O: Dict[Literal["FLH"], float]
    EL_STR: Dict[Literal["CAP_F"], float]
    H2_STR: Dict[Literal["CAP_F"], float]


def _create_example(t: type):
    """Generate example datastructure from type definition."""
    if isinstance(t, type):
        if issubclass(t, dict):  # TypedDict
            return {
                _create_example(k): _create_example(v)
                for k, v in t.__annotations__.items()
            }
        elif issubclass(t, str):
            # return random 3 character string
            return "".join(random.choices(string.ascii_uppercase, k=3))  # noqa S311
        elif issubclass(t, float):
            # return random float
            return round(random.random(), 3)  # noqa S311
    elif isinstance(t, str):
        return t
    elif get_origin(t) == list:  # List
        return [_create_example(v) for v in get_args(t)]
    elif get_origin(t) == dict:  # Dict
        k, v = get_args(t)
        return {_create_example(k): _create_example(v)}
    elif get_origin(t) == Literal:
        return _create_example(get_args(t)[0])
    raise NotImplementedError()


if __name__ == "__main__":
    print("Example OptInputDataType:")
    print(json.dumps(_create_example(OptInputDataType), indent=2))
    print("Example OptOutputDataType:")
    print(json.dumps(_create_example(OptOutputDataType), indent=2))
