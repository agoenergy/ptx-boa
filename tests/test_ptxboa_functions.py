# -*- coding: utf-8 -*-
"""Unittests for ptxboa_functions module."""

import logging
import unittest

import pandas as pd

import app.ptxboa_functions as pf
from ptxboa import DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI

logging.basicConfig(
    format="[%(asctime)s %(levelname)7s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.INFO,
)


class TestPtxboaFunctions(unittest.TestCase):
    def test_remove_subregions(self):
        """Test remove_subregions function."""
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
        api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
        df_in = api.get_dimension("region")

        # regions including subregions: 79
        self.assertEqual(len(df_in), 79)

        df_out = pf.remove_subregions(api, df_in, settings["country"])

        # output is dataframe:
        self.assertIsInstance(df_out, pd.DataFrame)

        # regions without subregions: 34
        self.assertEqual(len(df_out), 34)
        # Argentina should be in:
        self.assertTrue("Argentina" in df_out["region_name"])
        # Argentina (Buenos Aires) should be out:
        self.assertFalse("Argentina (Buenos Aires)" in df_out["region_name"])

        # if target country is also a source region, it needs to be removed
        # from the source region list:

        settings["country"] = "China"
        df_out = pf.remove_subregions(api, df_in, settings["country"])
        self.assertEqual(len(df_out), 33)
        self.assertFalse("China" in df_out["region_name"])
