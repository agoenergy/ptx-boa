# -*- coding: utf-8 -*-
"""Mockup streamlit app."""
# TODO how do I use the treamlit logger?
import logging

import pandas as pd
import streamlit as st

import app.ptxboa_functions as pf
from app.context_data import load_context_data
from app.sidebar import make_sidebar
from app.tab_certification_schemes import content_certification_schemes
from app.tab_country_fact_sheets import content_country_fact_sheets
from app.tab_dashboard import content_dashboard
from app.tab_deep_dive_countries import content_deep_dive_countries
from app.tab_disclaimer import content_disclaimer
from app.tab_input_data import content_input_data
from app.tab_literature import content_literature
from app.tab_market_scanning import content_market_scanning
from app.tab_sustainability import content_sustainability
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

if "user_changes_df" not in st.session_state:
    st.session_state["user_changes_df"] = None

if "edit_input_data" not in st.session_state:
    st.session_state["edit_input_data"] = False

st.set_page_config(layout="wide")
st.title("PtX Business Opportunity Analyzer :red[draft version, please do not quote!]")
if st.session_state["edit_input_data"]:
    st.warning("Data editing on")
    with st.expander("Modified data"):
        pf.display_user_changes()


(
    t_dashboard,
    t_market_scanning,
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
make_sidebar(api)

# import agora color scale:
if "colors" not in st.session_state:
    colors = pd.read_csv("data/Agora_Industry_Colours.csv")
    st.session_state["colors"] = colors["Hex Code"].to_list()

# calculate results over different data dimensions:
costs_per_region = pf.calculate_results_list(
    api,
    parameter_to_change="region",
    parameter_list=None,
    user_data=st.session_state["user_changes_df"],
)
costs_per_scenario = pf.calculate_results_list(
    api,
    parameter_to_change="scenario",
    parameter_list=None,
    user_data=st.session_state["user_changes_df"],
)
costs_per_res_gen = pf.calculate_results_list(
    api,
    parameter_to_change="res_gen",
    # TODO: here we remove PV tracking manually, this needs to be fixed in data
    parameter_list=[
        x for x in api.get_dimension("res_gen").index.to_list() if x != "PV tracking"
    ],
    user_data=st.session_state["user_changes_df"],
)
costs_per_chain = pf.calculate_results_list(
    api,
    parameter_to_change="chain",
    parameter_list=None,
    user_data=st.session_state["user_changes_df"],
)

# import context data:
cd = load_context_data()

# dashboard:
with t_dashboard:
    content_dashboard(
        api,
        costs_per_region=costs_per_region,
        costs_per_scenario=costs_per_scenario,
        costs_per_res_gen=costs_per_res_gen,
        costs_per_chain=costs_per_chain,
        context_data=cd,
    )

with t_market_scanning:
    content_market_scanning(api, costs_per_region)

with t_input_data:
    content_input_data(api)

with t_deep_dive_countries:
    content_deep_dive_countries(api, costs_per_region)

with t_country_fact_sheets:
    content_country_fact_sheets(cd)

with t_certification_schemes:
    content_certification_schemes(cd)

with t_sustainability:
    content_sustainability(cd)

with t_literature:
    content_literature(cd)

with t_disclaimer:
    content_disclaimer()
