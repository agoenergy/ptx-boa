"""Test utilities."""

import pandas as pd
from numpy import isclose


def assert_deep_equal(
    expected_result,
    actual_result,
    context: str = "",
    allow_new_dict_items: bool = False,
    sort_list_by_keys: list[str] | None = None,
):
    """Recursively compare nested data structure.

    - does not work for classes
    - almost equal for float
    """

    def _assert(comp, context=None):
        if not comp(expected_result, actual_result):
            raise ValueError(
                f"expected values {expected_result} != {actual_result} {context}"
            )

    if isinstance(expected_result, pd.DataFrame):
        if not isinstance(actual_result, pd.DataFrame):
            raise ValueError(f"Not a DataFrame: {type(actual_result)} {context}")
        expected_result = expected_result.to_dict(orient="records")
        actual_result = actual_result.to_dict(orient="records")

    if isinstance(expected_result, (str, int, bool, type(None), set)):
        # primitive
        _assert((lambda x, y: x == y), context)
    elif isinstance(expected_result, float):
        # float
        if not isinstance(actual_result, float):
            raise TypeError(f"Not a float: {type(actual_result)}: {actual_result}")
        _assert((lambda x, y: isclose(x, y, rtol=1e-8, equal_nan=True)), context)
    elif isinstance(expected_result, list):
        if not isinstance(actual_result, list):
            raise TypeError(f"Not a list: {type(actual_result)} {context}")
        if len(actual_result) != len(expected_result):
            print("===== EXP")
            print(sort_nested(expected_result))
            print("===== ACT")
            print(sort_nested(actual_result))
            raise ValueError(
                f"list length should be {len(expected_result)}, "
                f"not {len(actual_result)} {context}"
            )

        expected_result = _sort_list(
            expected_result, sort_list_by_keys=sort_list_by_keys
        )
        actual_result = _sort_list(actual_result, sort_list_by_keys=sort_list_by_keys)

        # recursion
        for i, (e, a) in enumerate(zip(expected_result, actual_result)):
            assert_deep_equal(
                e,
                a,
                context=f"{context} / {i}",
                allow_new_dict_items=allow_new_dict_items,
                sort_list_by_keys=sort_list_by_keys,
            )
    elif isinstance(expected_result, dict):
        if not isinstance(actual_result, dict):
            raise TypeError(f"Not a dict: {type(actual_result)} {context}")
        # compare keys
        if set(actual_result) != set(expected_result):
            missing_keys = set(expected_result) - set(actual_result)
            new_keys = set(actual_result) - set(expected_result)
            msg = "Dict keys not equal:"
            if missing_keys:
                msg += f" Missing: {missing_keys}"
            if new_keys:
                msg += f" New: {new_keys}"

            if missing_keys or (new_keys and not allow_new_dict_items):
                raise ValueError(f"{msg} {context}")

        # recursion
        for k, e in expected_result.items():
            a = actual_result[k]
            assert_deep_equal(
                e,
                a,
                context=f"{context} / {k}",
                allow_new_dict_items=allow_new_dict_items,
                sort_list_by_keys=sort_list_by_keys,
            )
    else:
        raise NotImplementedError(type(expected_result))


def _sort_list(xs: list, sort_list_by_keys: list[str] | None = None) -> list:
    return sorted(
        xs,
        key=lambda x: (
            tuple(x.get(k) for k in sort_list_by_keys or [])
            if isinstance(x, dict)
            else ()
        ),
    )


def sort_nested(xs, sort_list_by_keys: list[str] | None = None):
    if isinstance(xs, list):
        result = [sort_nested(x, sort_list_by_keys=sort_list_by_keys) for x in xs]
        return _sort_list(
            result,
            sort_list_by_keys=sort_list_by_keys,
        )

    elif isinstance(xs, dict):
        return {
            x: sort_nested(xs[x], sort_list_by_keys=sort_list_by_keys)
            for x in sorted(xs.keys())
        }
    else:
        return xs


def drop_null_nested(xs):
    if isinstance(xs, list):
        result = [drop_null_nested(x) for x in xs]
        result = [x for x in result if x]
        return result
    elif isinstance(xs, dict):
        result = {x: drop_null_nested(y) for x, y in xs.items()}
        # drop enire dict containing "values": 0
        if "values" in result and not result["values"]:
            result = {}
        else:
            result = {x: y for x, y in result.items() if y}
        return result
    else:
        return xs


def round_nested(xs, ndigis: int = 8):
    if isinstance(xs, list):
        result = [round_nested(x, ndigis) for x in xs]
        return result
    elif isinstance(xs, dict):
        result = {x: round_nested(y, ndigis) for x, y in xs.items()}
        return result
    elif isinstance(xs, float):
        return round(xs, ndigis)
    else:
        return xs


def assert_deep_equal_approx(
    expected,
    actually,
    ndigis: int = 8,
    context: str = "",
    allow_new_dict_items: bool = False,
    sort_list_by_keys: list[str] | None = None,
):

    expected = round_nested(drop_null_nested(expected), ndigis=ndigis)
    actually = round_nested(drop_null_nested(actually), ndigis=ndigis)

    try:
        assert_deep_equal(
            expected,
            actually,
            context=context,
            allow_new_dict_items=allow_new_dict_items,
            sort_list_by_keys=sort_list_by_keys,
        )
    except Exception:
        print("====================== OLD", context)
        print(sort_nested(expected))
        print("====================== NEW", context)
        # print so we can replace in test
        print(sort_nested(actually))
        print("======================")
        raise
