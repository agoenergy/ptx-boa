# -*- coding: utf-8 -*-
"""Unittests for ptxboa api module."""

import logging
import unittest

import numpy as np
import pytest

from ptxboa.api import PtxboaAPI
from ptxboa.api_calc import annuity
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

        # aggregate:
        res = res.groupby(["process_type", "cost_type"]).sum(["values"])

        return res

    def test_issue_145_undefined_cost_category(self):
        """See https://github.com/agoenergy/ptx-boa/issues/145."""
        settings = {
            "region": "United Arab Emirates",
            "country": "Germany",
            "chain": "Ammonia (AEL) + reconv. to H2",
            "res_gen": "PV tilted",
            "scenario": "2040 (medium)",
            "secproc_co2": "Direct Air Capture",
            "secproc_water": "Sea Water desalination",
            "transport": "Ship",
            "ship_own_fuel": False,
            "output_unit": "USD/t",
        }
        res = self._test_api_call(settings)
        level_cost_category = res.index.levels[0]
        self.assertFalse("" in level_cost_category, "empty value in cost_category")

    def test_example_api_call_1_ship(self):
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
        expected_result = {
            ("Water", "CAPEX"): 1.0949425140353066,
            ("Water", "OPEX"): 0.5313055092514363,
            ("Water", "FLOW"): 1.1785698932651663,
            ("Electrolysis", "CAPEX"): 263.57391257982044,
            ("Electrolysis", "OPEX"): 63.94777353767727,
            ("Electricity generation", "CAPEX"): 895.3287470389258,
            ("Electricity generation", "OPEX"): 304.11200849063624,
            ("Transportation (Ship)", "CAPEX"): 58.82535955280802,
            ("Transportation (Ship)", "OPEX"): 70.896276571698,
            ("Transportation (Ship)", "FLOW"): 104.72562247224381,
            ("Carbon", "CAPEX"): 188.70571332887613,
            ("Carbon", "OPEX"): 111.91943564963195,
            ("Carbon", "FLOW"): 99.10921639183132,
            ("Derivate production", "CAPEX"): 86.77905851250704,
            ("Derivate production", "OPEX"): 38.600831488868316,
            ("Heat", "FLOW"): 273.29119470172753,
            ("Electricity and H2 storage", "OPEX"): 169.95660780350494,
        }

        result_dict = {k: pytest.approx(v) for k, v in res_values.items() if v}

        assert expected_result == result_dict

    def test_example_api_call_2_ship_own_fuel(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "Argentina (Chaco)",
            "country": "Japan",
            "chain": "Methanol (SEOC)",
            "res_gen": "Wind Onshore",
            "scenario": "2040 (high)",
            "secproc_co2": "Specific costs",
            "secproc_water": "Sea Water desalination",
            "transport": "Ship",
            "ship_own_fuel": True,
            "output_unit": "USD/t",
        }
        res = self._test_api_call(settings)
        # test result categories
        res_values = res.groupby(["process_type", "cost_type"]).sum("values")["values"]
        expected_result = {
            ("Water", "CAPEX"): 1.1999586610376682,
            ("Water", "OPEX"): 0.21273242859187,
            ("Water", "FLOW"): 0.471894289243873,
            ("Electrolysis", "CAPEX"): 645.6608007889963,
            ("Electrolysis", "OPEX"): 85.8485762832237,
            ("Electricity generation", "CAPEX"): 1182.7977195898206,
            ("Electricity generation", "OPEX"): 146.78305821183,
            ("Transportation (Ship)", "OPEX"): 12.2061245592688,
            ("Carbon", "FLOW"): 61.3694736856213,
            ("Derivate production", "CAPEX"): 273.86577600899057,
            ("Derivate production", "OPEX"): 37.0003810701601,
            ("Derivate production", "FLOW"): 16.8369286421993,
            ("Electricity and H2 storage", "OPEX"): 54.435450052445674,
        }

        result_dict = {k: pytest.approx(v) for k, v in res_values.items() if v}

        assert expected_result == result_dict

    def test_example_api_call_3_pipeline_sea_land(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "Tunisia",
            "country": "Germany",
            "chain": "Hydrogen (PEM)",
            "res_gen": "Wind Offshore",
            "scenario": "2030 (high)",
            "secproc_co2": "Specific costs",
            "secproc_water": "Sea Water desalination",
            "transport": "Pipeline",
            "ship_own_fuel": False,
            "output_unit": "USD/MWh",
        }
        res = self._test_api_call(settings)
        # test result categories
        res_values = res.groupby(["process_type", "cost_type"]).sum("values")["values"]
        for k, v in {
            ("Water", "CAPEX"): 0.13940891490246338,
            ("Water", "OPEX"): 0.0301895762734038,
            ("Water", "FLOW"): 0.0669681098101092,
            ("Electrolysis", "CAPEX"): 35.966885352929644,
            ("Electrolysis", "OPEX"): 3.8943887822335106,
            ("Electrolysis", "FLOW"): 0,
            ("Electricity generation", "CAPEX"): 317.0098014700748,
            ("Electricity generation", "OPEX"): 58.3523144804189,
            ("Electricity generation", "FLOW"): 0,
            ("Transportation (Pipeline)", "CAPEX"): 7.5741225439209865,
            ("Transportation (Pipeline)", "OPEX"): 24.678148029682,
            ("Transportation (Pipeline)", "FLOW"): 2.97636043600485,
            ("Transportation (Ship)", "CAPEX"): 0,
            ("Transportation (Ship)", "OPEX"): 0,
            ("Transportation (Ship)", "FLOW"): 0,
            ("Carbon", "CAPEX"): 0,
            ("Carbon", "OPEX"): 0,
            ("Carbon", "FLOW"): 0,
            ("Derivate production", "CAPEX"): 0,
            ("Derivate production", "OPEX"): 0,
            ("Derivate production", "FLOW"): 0,
            ("Heat", "CAPEX"): 0,
            ("Heat", "OPEX"): 0,
            ("Heat", "FLOW"): 0,
            ("Electricity and H2 storage", "CAPEX"): 0,
            ("Electricity and H2 storage", "OPEX"): 2.7004897184631784,
            ("Electricity and H2 storage", "FLOW"): 0,
        }.items():
            self.assertAlmostEqual(res_values.get(k, 0), v, places=3, msg=k)

    def test_example_api_call_4_pipeline_retrofitted(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "Norway",
            "country": "Germany",
            "chain": "Hydrogen (PEM)",
            "res_gen": "Wind-PV-Hybrid",
            "scenario": "2030 (low)",
            "secproc_co2": "Specific costs",
            "secproc_water": "Specific costs",
            "transport": "Pipeline",
            "ship_own_fuel": False,
            "output_unit": "USD/MWh",
        }
        res = self._test_api_call(settings)
        # test result categories
        res_values = res.groupby(["process_type", "cost_type"]).sum("values")["values"]
        for k, v in {
            ("Water", "CAPEX"): 0,
            ("Water", "OPEX"): 0,
            ("Water", "FLOW"): 0.362589872395495,
            ("Electrolysis", "CAPEX"): 11.093600554061595,
            ("Electrolysis", "OPEX"): 2.8612504005382116,
            ("Electrolysis", "FLOW"): 0,
            ("Electricity generation", "CAPEX"): 25.55042024959996,
            ("Electricity generation", "OPEX"): 6.58993893072181,
            ("Electricity generation", "FLOW"): 0,
            ("Transportation (Pipeline)", "CAPEX"): 1.2357201482793199,
            ("Transportation (Pipeline)", "OPEX"): 2.55172143395481,
            ("Transportation (Pipeline)", "FLOW"): 0.710683430261875,
            ("Transportation (Ship)", "CAPEX"): 0,
            ("Transportation (Ship)", "OPEX"): 0,
            ("Transportation (Ship)", "FLOW"): 0,
            ("Carbon", "CAPEX"): 0,
            ("Carbon", "OPEX"): 0,
            ("Carbon", "FLOW"): 0,
            ("Derivate production", "CAPEX"): 0,
            ("Derivate production", "OPEX"): 0,
            ("Derivate production", "FLOW"): 0,
            ("Heat", "CAPEX"): 0,
            ("Heat", "OPEX"): 0,
            ("Heat", "FLOW"): 0,
            ("Electricity and H2 storage", "CAPEX"): 0,
            ("Electricity and H2 storage", "OPEX"): 1.783979520280975,
            ("Electricity and H2 storage", "FLOW"): 0,
        }.items():
            self.assertAlmostEqual(res_values.get(k, 0), v, places=3, msg=k)

    def test_api_get_input_data_output_format(self):
        """Test output structure of api.get_input_data()."""
        # test wrong scenario
        self.assertRaises(Exception, self.api.get_input_data, scenario="invalid")
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
        data_handler = DataHandler(scenario="2030 (low)", user_data=None)

        expected_val = 0.046

        # WACC without source_region_code (this is NOT fine)
        self.assertRaises(
            Exception, data_handler._get_parameter_value, parameter_code="WACC"
        )

        # WACC with process_code="" (this is fine)
        pval = data_handler._get_parameter_value(
            parameter_code="WACC", process_code="", source_region_code="AUS"
        )
        self.assertAlmostEqual(pval, expected_val)

        # WACC without process_code (this is fine)
        pval = data_handler._get_parameter_value(
            parameter_code="WACC", source_region_code="AUS"
        )
        self.assertAlmostEqual(pval, expected_val)

        # WACC without additional,non required field (this is fine)
        pval = data_handler._get_parameter_value(
            parameter_code="WACC",
            source_region_code="AUS",
            target_country_code="XYZ",
        )
        self.assertAlmostEqual(pval, expected_val)

        # FLH for other
        pval = data_handler._get_parameter_value(
            parameter_code="FLH",
            source_region_code="MAR-GUE",
            process_code="PEM-EL",
            process_code_res="WIND-OFF",
            process_code_ely="PEM-EL",
            process_code_deriv="LOHC-CON",
        )
        self.assertAlmostEqual(pval, 5436.92426314625)

        # FLH for RES
        pval = data_handler._get_parameter_value(
            parameter_code="FLH", source_region_code="ARG", process_code="PV-FIX"
        )
        self.assertAlmostEqual(pval, 1494.0)

        # test distances
        # FLH for RES
        pval = data_handler._get_parameter_value(
            parameter_code="DST-S-DP",
            source_region_code="ARE",
            target_country_code="DEU",
        )
        self.assertAlmostEqual(pval, 5500)

    def test_pmt(self):
        """Test if pmt function."""
        self.assertAlmostEqual(annuity(0, 100, 1), 0.01)
        self.assertAlmostEqual(annuity(0.1, 100, 1), 0.100007257098207)
        self.assertAlmostEqual(annuity(0.5, 100, 1), 0.5)
        self.assertAlmostEqual(annuity(1, 100, 1), 1)

        self.assertAlmostEqual(annuity(0.1, 10, 1), 0.162745394882512)
        self.assertAlmostEqual(annuity(0.5, 10, 1), 0.5088237828522)
        self.assertAlmostEqual(annuity(1, 10, 1), 1.0009775171)
