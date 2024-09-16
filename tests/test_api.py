# -*- coding: utf-8 -*-
"""Unittests for ptxboa api module."""

import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import pytest

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DataHandler
from ptxboa.utils import annuity

logging.basicConfig(
    format="[%(asctime)s %(levelname)7s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


ptxdata_dir_static = Path(__file__).parent / "test_data"


class TestApi(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        """Set up code for class."""
        cls.temp_dir = TemporaryDirectory()
        # create cahce dir (start context)
        cache_dir = cls.temp_dir.__enter__()
        cls.api = PtxboaAPI(data_dir=ptxdata_dir_static, cache_dir=cache_dir)

    @classmethod
    def tearDownClass(cls):
        """Tear down code for class."""
        # cleanup cache dir
        cls.temp_dir.__exit__(None, None, None)

    def _test_api_call(self, settings, optimize_flh=False):
        res, _metadata = self.api.calculate(**settings, optimize_flh=optimize_flh)
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

    def test_issue_317_demand_country_list_must_not_contain_supply_countries(self):
        """See https://github.com/agoenergy/ptx-boa/issues/317."""
        countries = self.api.get_dimension("country")
        self.assertFalse("Angola" in countries.index)

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
            ("Carbon", "CAPEX"): 215.39641925483323,
            ("Carbon", "FLOW"): 113.12731315531511,
            ("Carbon", "OPEX"): 127.74942135397198,
            ("Derivative production", "CAPEX"): 99.05316664855528,
            ("Derivative production", "OPEX"): 44.060567834906934,
            ("Electricity and H2 storage", "CAPEX"): 280.77888565912076,
            ("Electricity and H2 storage", "OPEX"): 1.3769573769647385,
            ("Electricity generation", "CAPEX"): 482.2723667527405,
            ("Electricity generation", "OPEX"): 99.456760428662,
            ("Electrolysis", "CAPEX"): 467.4703221865535,
            ("Electrolysis", "OPEX"): 113.41671110837947,
            ("Heat", "FLOW"): 311.94574723890867,
            ("Transportation (Ship)", "CAPEX"): 67.14567135002606,
            ("Transportation (Ship)", "FLOW"): 119.53810876643458,
            ("Transportation (Ship)", "OPEX"): 80.92390973573872,
            ("Water", "CAPEX"): 1.2624365339946522,
            ("Water", "FLOW"): 1.3588564441074482,
            ("Water", "OPEX"): 0.6125796349979609,
        }

        result_dict = {k: pytest.approx(v) for k, v in res_values.items() if v}

        assert expected_result == result_dict

    def test_example_api_call_2_ship_own_fuel(self):
        """Test output structure of api.calculate()."""
        settings = {
            "region": "Argentina (Chaco)",
            "country": "Japan",
            "chain": "Methanol (SOEC)",
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
            ("Carbon", "FLOW"): 70.62864261323912,
            ("Derivative production", "CAPEX"): 315.1854962423828,
            ("Derivative production", "FLOW"): 19.377213854990554,
            ("Derivative production", "OPEX"): 42.5828434596838,
            ("Electricity and H2 storage", "CAPEX"): 289.05606587378134,
            ("Electricity and H2 storage", "OPEX"): 0.5558849382145459,
            ("Electricity generation", "CAPEX"): 943.231485988988,
            ("Electricity generation", "OPEX"): 103.197961645443,
            ("Electrolysis", "CAPEX"): 970.5791481047149,
            ("Electrolysis", "OPEX"): 129.05048275062325,
            ("Transportation (Ship)", "OPEX"): 14.047733464451378,
            ("Water", "CAPEX"): 1.3949529227921325,
            ("Water", "FLOW"): 0.5485774963784155,
            ("Water", "OPEX"): 0.24730162185771912,
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
            ("Electricity and H2 storage", "CAPEX"): 45.95241145770308,
            ("Electricity and H2 storage", "OPEX"): 0.0,
            ("Electricity generation", "CAPEX"): 318.68449080388336,
            ("Electricity generation", "OPEX"): 55.11336801926485,
            ("Electrolysis", "CAPEX"): 67.95373961580324,
            ("Electrolysis", "OPEX"): 7.357831479534695,
            ("Transportation (Pipeline)", "CAPEX"): 8.71722456310389,
            ("Transportation (Pipeline)", "FLOW"): 3.425558822284455,
            ("Transportation (Pipeline)", "OPEX"): 28.402624453035553,
            ("Water", "CAPEX"): 0.160448792616752,
            ("Water", "FLOW"): 0.07707507350140025,
            ("Water", "OPEX"): 0.03474584868598187,
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
            ("Electricity and H2 storage", "CAPEX"): 18.462175001891314,
            ("Electricity and H2 storage", "OPEX"): 0.0,
            ("Electricity generation", "CAPEX"): 24.36897573382399,
            ("Electricity generation", "OPEX"): 8.4441424752989,
            ("Electrolysis", "CAPEX"): 21.00166954706848,
            ("Electrolysis", "OPEX"): 5.416729682187833,
            ("Transportation (Pipeline)", "CAPEX"): 1.4250719758145969,
            ("Transportation (Pipeline)", "FLOW"): 0.819582849362961,
            ("Transportation (Pipeline)", "OPEX"): 2.942726725527567,
            ("Water", "FLOW"): 0.4181502313322993,
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
        data_handler = DataHandler(
            scenario="2030 (low)",
            user_data=None,
            data_dir=ptxdata_dir_static,
            cache_dir=None,
        )

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

    def test_issue_553_storage_cost(self):
        """See https://github.com/agoenergy/ptx-boa/issues/553."""
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
        res = self._test_api_call(settings, optimize_flh=False)
        res_opt = self._test_api_call(settings, optimize_flh=True)
        self.assertAlmostEqual(
            res.at[("Electricity and H2 storage", "CAPEX"), "values"],
            896.432599,
            places=4,
        )
        self.assertAlmostEqual(
            res.at[("Electricity and H2 storage", "OPEX"), "values"], 4.396162, places=4
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "CAPEX"), "values"],
            221.907535,
            places=4,
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "OPEX"), "values"],
            6.732894,
            places=4,
        )


class TestRegression(unittest.TestCase):
    def test_issue_355_unique_index(self):
        """See https://github.com/agoenergy/ptx-boa/issues/355 ."""
        param_set = {
            "transport": "Ship",
            "ship_own_fuel": True,
            "secproc_water": "Sea Water desalination",
            "secproc_co2": "Direct Air Capture",
            "scenario": "2030 (high)",
            "country": "China",
            "res_gen": "PV tilted",
            "region": "United Arab Emirates",
            "chain": "Ammonia (AEL) + reconv. to H2",
        }
        api = PtxboaAPI(data_dir=ptxdata_dir_static)
        df = api.calculate(**param_set, optimize_flh=False)[0]
        df = df.set_index(
            [
                "process_type",
                "process_subtype",
                "cost_type",
                "scenario",
                "secproc_co2",
                "secproc_water",
                "chain",
                "res_gen",
                "region",
                "country",
                "transport",
            ]
        )
        self.assertTrue(
            df.index.is_unique,
            df.loc[df.index.duplicated()],
        )
