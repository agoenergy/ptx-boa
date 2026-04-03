"""Test utilities."""

from numpy import isclose


def assert_deep_equal(
    expected_result, actual_result, context=None, allow_new_dict_items: bool = False
):
    """Recursively compare nested data structure.

    - does not work for classes
    - almost equal for float
    """

    def _assert(comp, context=None):
        if not comp(expected_result, actual_result):
            raise ValueError(
                f"expected values {expected_result} != {actual_result} {context or ''}"
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
            assert_deep_equal(e, a, context, allow_new_dict_items=allow_new_dict_items)
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

            if missing_keys or (new_keys and not allow_new_dict_items):
                raise ValueError(msg)

        # recursion
        for k, e in expected_result.items():
            a = actual_result[k]
            assert_deep_equal(e, a, context, allow_new_dict_items=allow_new_dict_items)
    else:
        raise NotImplementedError(type(expected_result))


def sort_nested(xs):
    if isinstance(xs, list):
        return [sort_nested(x) for x in xs]
    elif isinstance(xs, dict):
        return {x: sort_nested(xs[x]) for x in sorted(xs.keys())}
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
    context=None,
    allow_new_dict_items: bool = False,
):
    expected = sort_nested(round_nested(drop_null_nested(expected), ndigis=ndigis))
    actually = sort_nested(round_nested(drop_null_nested(actually), ndigis=ndigis))
    print(actually)  # print so we can replace in test
    assert_deep_equal(
        expected, actually, context=context, allow_new_dict_items=allow_new_dict_items
    )
