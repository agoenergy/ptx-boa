"""Unittests for ptxboa api module."""

import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from ptxboa.api import PtxboaAPI
from ptxboa.api_data import DataHandler
from ptxboa.utils import annuity
from tests.utils import assert_deep_equal_approx

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
        res = self.api.calculate(**settings, optimize_flh=optimize_flh).costs
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
        print(res)
        self.assertFalse(
            "" in level_cost_category, "empty value in cost_category (process_type)"
        )

    def test_issue_317_demand_country_list_must_not_contain_supply_countries(self):
        """See https://github.com/agoenergy/ptx-boa/issues/317."""
        countries = self.api.get_dimension("country", tool_version_color="green")
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
            ("Carbon", "CAPEX"): 196.01309835,
            ("Carbon", "OPEX"): 116.25337124,
            ("Derivative production", "CAPEX"): 90.13946547,
            ("Derivative production", "OPEX"): 40.09559883,
            ("Electricity and H2 storage", "CAPEX"): 255.51185818,
            ("Electricity and H2 storage", "OPEX"): 1.25304628,
            ("Electricity generation", "CAPEX"): 482.27236675,
            ("Electricity generation", "OPEX"): 99.45676043,
            ("H2 production", "CAPEX"): 425.40310817,
            ("H2 production", "OPEX"): 103.21044809,
            ("Heat", "FLOW"): 283.87404324,
            ("Transportation (Ship)", "CAPEX"): 61.10329562,
            ("Transportation (Ship)", "FLOW"): 1.82382412,
            ("Transportation (Ship)", "OPEX"): 73.64164331,
            ("Water", "CAPEX"): 1.14883106,
            ("Water", "OPEX"): 0.55745417,
        }
        res_values = dict(res_values.items())
        assert_deep_equal_approx(expected_result, res_values)

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
            ("Carbon", "FLOW"): 69.057413040518,
            ("Derivative production", "CAPEX"): 308.1737690695886,
            ("Derivative production", "OPEX"): 41.63553057840994,
            ("Electricity and H2 storage", "CAPEX"): 279.89262037545114,
            ("Electricity and H2 storage", "OPEX"): 0.5435185267752691,
            ("Electricity generation", "CAPEX"): 842.7006740519129,
            ("Electricity generation", "OPEX"): 92.19899158499206,
            ("H2 production", "CAPEX"): 939.4974306861657,
            ("H2 production", "OPEX"): 124.91778461321229,
            ("Transportation (Ship)", "OPEX"): 13.735222655346394,
            ("Water", "CAPEX"): 1.3502811073682484,
            ("Water", "OPEX"): 0.23938206254847536,
        }

        res_values = dict(res_values.items())
        assert_deep_equal_approx(expected_result, res_values)

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

        expected_result = {
            ("Electricity and H2 storage", "CAPEX"): 44.84637867437069,
            ("Electricity generation", "CAPEX"): 287.5830863315742,
            ("Electricity generation", "OPEX"): 49.73468408558943,
            ("H2 production", "CAPEX"): 66.31815485798717,
            ("H2 production", "OPEX"): 7.180735162443889,
            ("Transportation (Pipeline)", "CAPEX"): 8.507408889875556,
            ("Transportation (Pipeline)", "OPEX"): 27.71899909407804,
            ("Water", "CAPEX"): 0.15658693599049908,
            ("Water", "OPEX"): 0.03390954768430808,
        }

        res_values = dict(res_values.items())
        assert_deep_equal_approx(expected_result, res_values)

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
        expected_result = {
            ("Electricity and H2 storage", "CAPEX"): 18.35151536,
            ("Electricity generation", "CAPEX"): 24.36897573,
            ("Electricity generation", "OPEX"): 8.44414248,
            ("H2 production", "CAPEX"): 20.87578854,
            ("H2 production", "OPEX"): 5.38426258,
            ("Transportation (Pipeline)", "CAPEX"): 1.4165303,
            ("Transportation (Pipeline)", "OPEX"): 2.92508844,
            ("Water", "FLOW"): 0.4156439,
        }

        res_values = dict(res_values.items())
        assert_deep_equal_approx(expected_result, res_values)

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
            process_res="WIND-OFF",
            process_ely="PEM-EL",
            process_deriv="LOHC-CON",
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
            823.7733133374624,
            places=4,
        )
        self.assertAlmostEqual(
            res.at[("Electricity and H2 storage", "OPEX"), "values"],
            4.079589637694555,
            places=4,
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "CAPEX"), "values"],
            183.481609334802,
            places=4,
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "OPEX"), "values"],
            5.567013499284561,
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
        df = api.calculate(**param_set, optimize_flh=False).costs
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
