# -*- coding: utf-8 -*-
"""Mockup streamlit app."""
# TODO how do I use the treamlit logger?
import logging

import pandas as pd
import streamlit as st

import app.ptxboa_functions as pf
from ptxboa.api import PtxboaAPI

# setup logging
# level can be changed on strartup with: --logger.level=LEVEL
loglevel = st.logger.get_logger(__name__).level


logger = logging.getLogger()  # do not ude __name__ so we can resue it in submodules
logger.setLevel(loglevel)
log_handler = logging.StreamHandler()
log_handler.setFormatter(
    logging.Formatter(
        "[%(asctime)s %(levelname)7s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
)
logger.addHandler(log_handler)


logger.info("Updating app...")


# app layout:

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)

st.set_page_config(layout="wide")
st.title("PtX Business Opportunity Analyzer :red[draft version, please do not quote!]")
(
    t_dashboard,
    t_market_scanning,
    t_costs_by_region,
    t_input_data,
    t_deep_dive_countries,
    t_country_fact_sheets,
    t_certification_schemes,
    t_sustainability,
    t_literature,
    t_disclaimer,
) = st.tabs(
    [
        "Dashboard",
        "Market scanning",
        "Costs by region",
        "Input data",
        "Deep-dive countries",
        "Country fact sheets",
        "Certification schemes",
        "Sustainability",
        "Literature",
        "Disclaimer",
    ]
)


api = st.cache_resource(PtxboaAPI)()

# create sidebar:
settings = pf.create_sidebar(api)

# calculate results:
res_details = pf.calculate_results(
    api,
    settings,
)
res_costs = pf.aggregate_costs(res_details)

# import context data:
cd = st.cache_resource(pf.import_context_data)()

# dashboard:
with t_dashboard:
    pf.content_dashboard(api, res_costs, cd, settings)

with t_market_scanning:
    pf.content_market_scanning(api, res_costs, settings)

with t_costs_by_region:
    pf.content_costs_by_region(api, res_costs, settings)

with t_input_data:
    pf.content_input_data(api, settings)

with t_deep_dive_countries:
    pf.content_deep_dive_countries(api, res_costs, settings)

with t_country_fact_sheets:
    pf.create_fact_sheet_demand_country(cd, settings["country"])
    st.divider()
    pf.create_fact_sheet_supply_country(cd, settings["region"])

with t_certification_schemes:
    pf.create_fact_sheet_certification_schemes(cd)

with t_sustainability:
    pf.create_content_sustainability(cd)

with t_literature:
    pf.create_content_literature(cd)

with t_disclaimer:
    pf.content_disclaimer()
