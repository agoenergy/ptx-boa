"""Unittests for ptxboa api module."""

import logging
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from ptxboa.api import PtxboaAPI, _translate_and_validate_user_settings
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
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
            ("Electricity generation", "CAPEX"): 504.63962363,
            ("Electricity generation", "OPEX"): 104.06945455,
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
            ("Carbon", "FLOW"): 69.05741304,
            ("Derivative production", "CAPEX"): 308.17376907,
            ("Derivative production", "OPEX"): 41.63553058,
            ("Electricity and H2 storage", "CAPEX"): 282.62562318,
            ("Electricity and H2 storage", "OPEX"): 0.54351853,
            ("Electricity generation", "CAPEX"): 994.06874845,
            ("Electricity generation", "OPEX"): 108.76001289,
            ("H2 production", "CAPEX"): 948.98730372,
            ("H2 production", "OPEX"): 126.17958042,
            ("Transportation (Ship)", "OPEX"): 13.73522266,
            ("Water", "CAPEX"): 1.36392031,
            ("Water", "OPEX"): 0.24180006,
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
            ("Electricity and H2 storage", "CAPEX"): 44.84637867,
            ("Electricity generation", "CAPEX"): 318.6844908,
            ("Electricity generation", "OPEX"): 55.11336802,
            ("H2 production", "CAPEX"): 66.31815486,
            ("H2 production", "OPEX"): 7.18073516,
            ("Transportation (Pipeline)", "CAPEX"): 8.50740889,
            ("Transportation (Pipeline)", "OPEX"): 27.71899909,
            ("Water", "CAPEX"): 0.15658694,
            ("Water", "OPEX"): 0.03390955,
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
            831.8795131795181,
            places=4,
        )
        self.assertAlmostEqual(
            res.at[("Electricity and H2 storage", "OPEX"), "values"],
            4.079589637694555,
            places=4,
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "CAPEX"), "values"],
            338.80543452051774,
            places=4,
        )
        self.assertAlmostEqual(
            res_opt.at[("Electricity and H2 storage", "OPEX"), "values"],
            7.628877979749411,
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

    def test_issue_823_no_transport(self):
        """No transportation cost when supply_country == demand_country.

        When transport distance is zero.
        (e.g. supply_country = Brazil & demand_country = Brazil) there are still
        costs associated with transportation in the results.
        This is due to the pre- and post-transportation conversion processes,
        which get calculated even though they are not necessary.
        """
        # import region == export country:
        country_region = "Brazil"
        for transport in {"Ship", "Pipeline"}:
            param_set = {
                "transport": transport,  # will be ignored / changed to "NONE"
                "ship_own_fuel": True,
                "secproc_water": "Specific costs",
                "secproc_co2": "Direct Air Capture (blue)",
                "scenario": "2030 (medium)",
                "res_gen": None,
                "chain": "H2-G__ATR_91%__prod_in_supply",
                "country": country_region,
                "region": country_region,
            }

            chain_def, _tool_version_color, _optimize_flh = (
                _translate_and_validate_user_settings(**param_set, optimize_flh=False)
            )
            self.assertEqual(chain_def.transport, "NONE")

            # api.calculate should work
            api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
            df_costs = api.calculate(**param_set, optimize_flh=False).costs

            # we should not get transportation costs
            assert not any(
                "transportation" in x.lower() for x in df_costs["process_type"]
            )

    def test_switch_pipeline(self):
        """Switch to Ship if pipeline does not exist."""
        param_set = {
            "transport": "Pipeline",
            "ship_own_fuel": True,
            "secproc_water": "Specific costs",
            "secproc_co2": "Direct Air Capture (blue)",
            "scenario": "2030 (medium)",
            "res_gen": None,
            "chain": "H2-G__ATR_91%__prod_in_supply",
            "region": "Australia",
            "country": "Germany",
        }

        chain_def, _tool_version_color, _optimize_flh = (
            _translate_and_validate_user_settings(**param_set, optimize_flh=False)
        )
        self.assertEqual(chain_def.transport, "Ship")
