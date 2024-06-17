# -*- coding: utf-8 -*-
"""Utilities."""
import json
import os
from types import NoneType
from typing import Union


def annuity(rate: float, periods: int, value: float) -> float:
    """Calculate annuity.

    Parameters
    ----------
    rate: float
        interest rate per period
    periods: int
        number of periods
    value: float
        present value of an ordinary annuity

    Returns
    -------
    : float
        value of each payment

    """
    if rate == 0:
        return value / periods
    else:
        return value * rate / (1 - (1 / (1 + rate) ** periods))


class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args):
        """Create a new instance only if not exist.

        NOTE: no **kwargs allowed, because we need to create hashable key
        """
        key = (cls, args)
        if key not in cls._instances:
            cls._instances[key] = super().__call__(*args)
        return cls._instances[key]


def is_test():
    return (
        "PYTEST_CURRENT_TEST" in os.environ
        or "STREAMLIT_GLOBAL_UNIT_TEST" in os.environ
    )


def serialize_for_hashing(
    obj: Union[NoneType, int, float, str, bool, dict, list], float_sig_digits=6
) -> str:
    """Serialize data for hashing.

    - custom function to ensure same results for differrent python versions
        (json dumps changes sometimes?)
    -

    Parameters
    ----------
    obj : Union[NoneType, int, float, str, dict, list]
        data
    float_sig_digits : int, optional
        number of significat digits (in scientific notation)

    Returns
    -------
    str
        string serialization
    """
    if isinstance(obj, list):
        return "[" + ",".join(serialize_for_hashing(x) for x in obj) + "]"
    elif isinstance(obj, dict):
        # map keys to sorted
        obj_ = {
            serialize_for_hashing(k): serialize_for_hashing(v) for k, v in obj.items()
        }
        return "{" + ",".join(k + ":" + v for k, v in sorted(obj_.items())) + "}"
    elif isinstance(obj, bool):
        # NOTE: MUST come before test for
        return "true" if obj is True else "false"
    elif isinstance(obj, str):
        # use json to take care of line breaks and other escaping
        return json.dumps(obj, ensure_ascii=False)
    elif isinstance(obj, int):
        return str(obj)
    elif isinstance(obj, float):
        return f"%.{float_sig_digits}e" % obj
    elif obj is None:
        return "null"
    else:
        raise NotImplementedError(type(obj))
