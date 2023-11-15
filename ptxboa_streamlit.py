# -*- coding: utf-8 -*-
"""Mockup streamlit app."""
import pandas as pd
import streamlit as st

import app.ptxboa_functions as pf
from app.context_data import load_context_data
from app.sidebar import make_sidebar
from app.tab_certification_schemes import content_certification_schemes
from app.tab_country_fact_sheets import content_country_fact_sheets
from app.tab_dashboard import content_dashboard
from app.tab_disclaimer import content_disclaimer
from app.tab_literature import content_literature
from app.tab_sustainability import content_sustainability
from ptxboa.api import PtxboaAPI

# app layout:

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)

if "user_changes_df" not in st.session_state:
    st.session_state["user_changes_df"] = None

st.set_page_config(layout="wide")
st.title("PtX Business Opportunity Analyzer :red[draft version, please do not quote!]")
(
    t_dashboard,
    t_market_scanning,
    t_compare_costs,
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
        "Compare costs",
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

if st.session_state["edit_input_data"] is False:
    pf.reset_user_changes()

# import agora color scale:
if "colors" not in st.session_state:
    colors = pd.read_csv("data/Agora_Industry_Colours.csv")
    st.session_state["colors"] = colors["Hex Code"].to_list()

# calculate results:
res_costs = pf.calculate_results_list(
    api, "region", user_data=st.session_state["user_changes_df"]
)

# import context data:
cd = load_context_data()

# dashboard:
with t_dashboard:
    content_dashboard(api, res_costs, cd)

with t_market_scanning:
    pf.content_market_scanning(api, res_costs)

with t_compare_costs:
    pf.content_compare_costs(api, res_costs)

with t_input_data:
    pf.content_input_data(api)

with t_deep_dive_countries:
    pf.content_deep_dive_countries(api, res_costs)

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
