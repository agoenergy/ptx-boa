# -*- coding: utf-8 -*-
"""Utilities."""

import os


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
