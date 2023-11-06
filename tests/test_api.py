# -*- coding: utf-8 -*-
"""Unittests for ptxboa api module."""

import logging
import unittest

import numpy as np

from ptxboa.api import PtxboaAPI
from ptxboa.api_calc import pmt
from ptxboa.api_data import DataHandler

logging.basicConfig(
    format="[%(asctime)s %(levelname)7s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up code for class."""
        cls.api = PtxboaAPI()

    def _test_api_call(self, settings):
        res = self.api.calculate(**settings)
        # test that settings are in results
        for k, v in settings.items():
            if k in ["ship_own_fuel", "output_unit"]:  # skip some
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

        return res

    def test_example_api_call(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "United Arab Emirates",
            "country": "Germany",
            "chain": "Methane (AEL)",
            "res_gen": "PV tilted",
            "scenario": "2040 (medium)",
            "secproc_co2": "Direct Air Capture",
            "secproc_water": "Sea Water desalination",
            "transport": "Ship",
            "ship_own_fuel": False,
            "output_unit": "USD/t",
        }
        res = self._test_api_call(settings)
        # test result categories
        res_values = res.groupby(["process_type", "cost_type"]).sum("values")["values"]
        for k, v in {
            ("Water", "CAPEX"): 1.13421722706732,
            ("Water", "OPEX"): 0.539157778349926,
            ("Water", "FLOW"): 1.19598821058383,
            ("Electrolysis", "CAPEX"): 290.29664931801,
            ("Electrolysis", "OPEX"): 68.9972312065034,
            ("Electrolysis", "FLOW"): 0,
            ("Electricity generation", "CAPEX"): 927.443473756068,
            ("Electricity generation", "OPEX"): 308.606539951669,
            ("Electricity generation", "FLOW"): 0,
            ("Transportation (Pipeline)", "CAPEX"): 0,
            ("Transportation (Pipeline)", "OPEX"): 0,
            ("Transportation (Pipeline)", "FLOW"): 0,
            ("Transportation (Ship)", "CAPEX"): 61.3537645039656,
            ("Transportation (Ship)", "OPEX"): 71.154090224582,
            ("Transportation (Ship)", "FLOW"): 106.247433353769,
            ("Carbon", "CAPEX"): 196.816576798637,
            ("Carbon", "OPEX"): 113.573515102545,
            ("Carbon", "FLOW"): 100.573971083243,
            ("Derivate production", "CAPEX"): 90.5089566868282,
            ("Derivate production", "OPEX"): 39.171320804334,
            ("Derivate production", "FLOW"): 0,
            ("Heat", "CAPEX"): 0,
            ("Heat", "OPEX"): 0,
            ("Heat", "FLOW"): 277.330219266086,
            ("Electricity and H2 storage", "CAPEX"): 0,
            ("Electricity and H2 storage", "OPEX"): 176.381710654865,
            ("Electricity and H2 storage", "FLOW"): 0,
        }.items():
            self.assertAlmostEqual(res_values.get(k, 0), v, places=3, msg=k)

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

        # test distances
        # FLH for RES
        pval = data_handler.get_parameter_value(
            parameter_code="DST-S-DP",
            source_region_code="ARE",
            target_country_code="DEU",
        )
        self.assertAlmostEqual(pval, 5500)

    def test_pmt(self):
        """Test if pmt function."""
        self.assertAlmostEqual(pmt(0, 100, 1), 0.01)
        self.assertAlmostEqual(pmt(0.1, 100, 1), 0.100007257098207)
        self.assertAlmostEqual(pmt(0.5, 100, 1), 0.5)
        self.assertAlmostEqual(pmt(1, 100, 1), 1)

        self.assertAlmostEqual(pmt(0.1, 10, 1), 0.162745394882512)
        self.assertAlmostEqual(pmt(0.5, 10, 1), 0.5088237828522)
        self.assertAlmostEqual(pmt(1, 10, 1), 1.0009775171)
