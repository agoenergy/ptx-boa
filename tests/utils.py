# -*- coding: utf-8 -*-
"""Test utilities."""

from numpy import isclose


def assert_deep_equal(expected_result, actual_result, context=None):
    """Recursively compare nested data structure.

    - does not work for classes
    - almost equal for float
    """

    def _assert(comp, context=None):
        if not comp(expected_result, actual_result):
            raise ValueError(
                f"expected values {expected_result} != "
                f"{actual_result} {context or ''}"
            )

    if isinstance(expected_result, (str, int, bool, type(None), set)):
        # primitive
        _assert((lambda x, y: x == y), context)
    elif isinstance(expected_result, float):
        # float
        _assert((lambda x, y: isclose(x, y, rtol=1e-6, equal_nan=True)), context)
    elif isinstance(expected_result, list):
        if not isinstance(actual_result, list):
            raise ValueError(f"Not a list: {expected_result}")
        if len(actual_result) != len(expected_result):
            raise ValueError(
                f"list length should be {len(expected_result)}, "
                f"not {len(actual_result)}"
            )
        # recursion
        for e, a in zip(expected_result, actual_result):
            assert_deep_equal(e, a, context)
    elif isinstance(expected_result, dict):
        if not isinstance(actual_result, dict):
            raise ValueError(f"Not a dict: {expected_result}")
        # compare keys
        if set(actual_result) != set(expected_result):
            missing_keys = set(expected_result) - set(actual_result)
            new_keys = set(actual_result) - set(expected_result)
            msg = "Dict keys not equal:"
            if missing_keys:
                msg += f" Missing: {missing_keys}"
            if new_keys:
                msg += f" New: {new_keys}"
            raise ValueError(msg)
        # recursion
        for k, e in expected_result.items():
            a = actual_result[k]
            assert_deep_equal(e, a, context)
    else:
        raise NotImplementedError(type(expected_result))
