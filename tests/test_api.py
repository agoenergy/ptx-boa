# coding: utf-8
import unittest
import numpy as np

from ptxboa.api import PtxboaAPI


class TestTemplate(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    @classmethod
    def setUpClass(cls):
        cls.api = PtxboaAPI()

    @classmethod
    def tearDownClass(cls):
        pass

    def _test_api_call(self, settings):
        res = self.api.calculate(**settings)
        # test that settings are in results
        for k, v in settings.items():
            if k in ["ship_own_fuel"]:  # skip some
                continue
            self.assertEqual(
                set(res[k].unique()), set([v]), f"wrong data in dimension column: {k}"
            )
        # test expected output columns
        for k in ["values"]:
            self.assertTrue(k in res.columns)

    def test_example_api_call(self):
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
        # test wrong scenario
        self.assertRaises(ValueError, self.api.get_input_data, scenario="invalid")
        # test output structure of data
        res = self.api.get_input_data("2030 (high)", long_names=False)
        self.assertEqual(
            set(res.columns),
            set(
                [
                    "parameter_code",
                    "process_code",
                    "flow_code",
                    "source_region_code",
                    "target_country_code",
                    "value",
                    "unit",
                    "source",
                ]
            ),
        )

    def test_get_input_data_nan_consistency(self):
        res = self.api.get_input_data("2030 (high)", long_names=False)
        self.assertEqual(
            set(res.columns),
            set(
                [
                    "parameter_code",
                    "process_code",
                    "flow_code",
                    "source_region_code",
                    "target_country_code",
                    "value",
                    "unit",
                    "source",
                ]
            ),
        )
        # test nans are at same place
        changed_columns = [
            "parameter_code",
            "process_code",
            "flow_code",
            "source_region_code",
            "target_country_code",
        ]
        for scenario in ["2030 (low)", "2030 (medium)", "2030 (high)", "2040 (low)", "2040 (medium)", "2040 (high)"]:
            left = self.api.get_input_data(scenario, long_names=False)[changed_columns].values == ""
            right = self.api.get_input_data(scenario, long_names=True)[changed_columns].isna().values
            self.assertTrue(np.all(left == right))