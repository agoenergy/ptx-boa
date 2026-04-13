"""Tests for utils module."""

import json
import unittest

import pandas as pd

from ptxboa.utils import serialize_for_hashing

from .utils import assert_deep_equal, assert_deep_equal_approx


class TestUtils(unittest.TestCase):
    """Tests for utils module."""

    def test_assert_deep_equal(self):
        """Test for utils.assert_deep_equal."""
        assert_deep_equal(1, 1)
        assert_deep_equal("a", "a")
        assert_deep_equal(True, True)
        self.assertRaises(ValueError, assert_deep_equal, 1, 2)
        self.assertRaises(ValueError, assert_deep_equal, "a", "b")
        self.assertRaises(ValueError, assert_deep_equal, True, False)
        self.assertRaises(ValueError, assert_deep_equal, 1, "1")
        assert_deep_equal(1.2, 1.2)
        self.assertRaises(ValueError, assert_deep_equal, 1.2, 1.20001)
        assert_deep_equal([1, 2], [1, 2])
        assert_deep_equal({"a": [], "b": 1.2}, {"a": [], "b": 1.200000001})
        self.assertRaises(TypeError, assert_deep_equal, [], {})
        self.assertRaises(ValueError, assert_deep_equal, [], [1])
        self.assertRaises(ValueError, assert_deep_equal, {"a": 1}, {"b": 1})
        self.assertRaises(ValueError, assert_deep_equal, {"a": 1}, {"a": 2})

    def test_serialize_for_hashing(self):
        """Test for ptxboa.utils.serialize_for_hashing."""
        for obj, exp_str in [
            ("text", '"text"'),
            (123, "123"),
            (123.0, "1.230000e+02"),
            (-123.0, "-1.230000e+02"),
            (-123.4567, "-1.234567e+02"),
            (0.0000001234567, "1.234567e-07"),
            (True, "true"),
            (False, "false"),
            ([], "[]"),
            ({}, "{}"),
            ([1, {"b": 2, "a": [None]}], '[1,{"a":[null],"b":2}]'),
        ]:
            res = serialize_for_hashing(obj)
            # must be json loadable
            json.loads(res)
            self.assertEqual(res, exp_str)

    def test_assert_deep_equal_sort_list_by_keys(self):
        """Test comparison of list sorting."""
        data = [{"x": 1}, {"x": 2}]
        data_rev = list(reversed(data))

        self.assertRaises(Exception, assert_deep_equal, data, data_rev)
        assert_deep_equal(data, data_rev, sort_list_by_keys=["x"])

    def test_assert_deep_equal_dataframe(self):
        """Test comparison of DataFrame."""
        data = [{"x": 1}, {"x": 2}, {"x": 3}]
        df = pd.DataFrame(data)
        assert_deep_equal_approx(data, df)
        self.assertRaises(Exception, assert_deep_equal_approx, df, pd.DataFrame())
