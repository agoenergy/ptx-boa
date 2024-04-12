# -*- coding: utf-8 -*-
"""Tests for utils module."""
import unittest

from .utils import assert_deep_equal


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
        assert_deep_equal({"a": [], "b": 1.2}, {"a": [], "b": 1.2000001})
        self.assertRaises(ValueError, assert_deep_equal, [], {})
        self.assertRaises(ValueError, assert_deep_equal, [], [1])
        self.assertRaises(ValueError, assert_deep_equal, {"a": 1}, {"b": 1})
        self.assertRaises(ValueError, assert_deep_equal, {"a": 1}, {"a": 2})
