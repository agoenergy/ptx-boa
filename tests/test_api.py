# -*- coding: utf-8 -*-
"""Unittests for ptxboa api module."""

import unittest

import numpy as np

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DataHandler


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up code for class."""
        cls.api = PtxboaAPI()

    def _test_api_call(self, settings):
        res = self.api.calculate(**settings)
        # test that settings are in results
        for k, v in settings.items():
            if k in ["ship_own_fuel"]:  # skip some
                continue
            self.assertEqual(
                set(res[k].unique()), {v}, f"wrong data in dimension column: {k}"
            )
        # test expected additional output columns
        for k in [
            "values",
            "process_type",
            "process_subtype",
            "cost_type",
        ]:
            self.assertTrue(k in res.columns)

    def test_example_api_call(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "Argentina",
            "country": "China",
            "chain": "Ammonia (AEL)",
            "res_gen": "PV tilted",
            "scenario": "2040 (medium)",
            "secproc_co2": "Direct Air Capture",
            "secproc_water": "Sea Water desalination",
            "transport": "Ship",
            "ship_own_fuel": False,
        }
        self._test_api_call(settings)

    def test_api_get_input_data_output_format(self):
        """Test output structure of api.get_input_data()."""
        # test wrong scenario
        self.assertRaises(ValueError, self.api.get_input_data, scenario="invalid")
        # test output structure of data
        res = self.api.get_input_data("2030 (high)", long_names=False)
        self.assertEqual(
            set(res.columns),
            {
                "parameter_code",
                "process_code",
                "flow_code",
                "source_region_code",
                "target_country_code",
                "value",
                "unit",
                "source",
            },
        )

    def test_get_input_data_nan_consistency(self):
        """Test nans are at same place."""
        changed_columns = [
            "parameter_code",
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ]
        for scenario in [
            "2030 (low)",
            "2030 (medium)",
            "2030 (high)",
            "2040 (low)",
            "2040 (medium)",
            "2040 (high)",
        ]:
            left = (
                self.api.get_input_data(scenario, long_names=False)[
                    changed_columns
                ].values
                == ""
            )
            right = (
                self.api.get_input_data(scenario, long_names=True)[
                    changed_columns
                ].values
                == ""
            )
            self.assertTrue(np.all(left == right))

    def test_datahandler(self):
        """Test functionality for DataHandler.get_parameter_value."""
        data_handler = DataHandler(self.api.data, scenario="2030 (low)", user_data=None)

        expected_val = 0.0503

        # WACC without source_region_code (this is NOT fine)
        self.assertRaises(
            Exception, data_handler.get_parameter_value, parameter_code="WACC"
        )

        # WACC with process_code="" (this is fine)
        pval = data_handler.get_parameter_value(
            parameter_code="WACC", process_code="", source_region_code="AUS"
        )
        self.assertAlmostEqual(pval, expected_val)

        # WACC without process_code (this is fine)
        pval = data_handler.get_parameter_value(
            parameter_code="WACC", source_region_code="AUS"
        )
        self.assertAlmostEqual(pval, expected_val)

        # WACC without additional,non required field (this is fine)
        pval = data_handler.get_parameter_value(
            parameter_code="WACC",
            source_region_code="AUS",
            target_country_code="XYZ",
        )
        self.assertAlmostEqual(pval, expected_val)

        # FLH for other
        pval = data_handler.get_parameter_value(
            parameter_code="FLH",
            source_region_code="MAR-GUE",
            process_code="PEM-EL",
            process_code_res="WIND-OFF",
            process_code_ely="PEM-EL",
            process_code_deriv="LOHC-CON",
        )
        self.assertAlmostEqual(pval, 5436.92426314625)

        # FLH for RES
        pval = data_handler.get_parameter_value(
            parameter_code="FLH", source_region_code="ARG", process_code="PV-FIX"
        )
        self.assertAlmostEqual(pval, 1494.0)
