# -*- coding: utf-8 -*-
"""Type definitions."""

import json
import random
import string
from typing import Dict, List, Literal, TypedDict, get_args, get_origin

ProcessCodeResType = Literal["PV-FIX", "PV-TRK", "RES-HYBR", "WIND-OFF", "WIND-ON"]


class ProcessElyInputDataType(TypedDict):
    EFF: float
    CAPEX_A: float
    OPEX_F: float
    OPEX_O: float
    Dict[Literal["H2O"], float]


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


class OptInputDataType(TypedDict):
    SOURCE_REGION_CODE: str
    RES: List[ProcessResInputDataType]
    ELY: ProcessElyInputDataType
    EL_STR: ProcessStorageInputDataType
    H2_STR: ProcessStorageInputDataType
    SPECCOST: Dict[Literal["H2O"], float]


class ProcessOutputResType(TypedDict):
    SHARE_FACTOR: float
    FLH: float
    PROCESS_CODE: ProcessCodeResType


class OptOutputDataType(TypedDict):
    RES: List[ProcessOutputResType]
    ELY: Dict[Literal["FLH"], float]
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
