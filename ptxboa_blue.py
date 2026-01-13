"""Content of blue Ptx subpage."""

import streamlit as st
import streamlit_antd_components as sac

from app.layout_elements import display_footer
from app.sidebar import make_sidebar
from ptxboa import DEFAULT_CACHE_DIR, DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI

api = st.cache_resource(PtxboaAPI)(
    data_dir=DEFAULT_DATA_DIR,
    cache_dir=DEFAULT_CACHE_DIR,
)

st.set_page_config(
    page_title="Blue PtX Business Opportunity Analyser",
    page_icon="./data/favicon-16x16.png",
)
st.title("Blue PtX Business Opportunity Analyser")

tabs = (
    "Info",
    "Overview",
    "Costs",
    "Emissions",
    "Market scanning",
    "Input data",
    "Country fact sheets",
    "Certification schemes",
    "Sustainability",
    "Literature",
)

tabs_icons = {
    "Overview": "house-fill",
    "Info": "question-circle-fill",
}

# the "tab_key" is used to identify the sac.tabs element. Whenever a tab is switched
# programatically (e.g. via app.ptxboa.functions.move_to_tab), the "tab_key" entry is
# incremented by 1. This allows us to set the programatically set tab as the default
# `index` in `sac.tabs()`.
if "tab_key" not in st.session_state:
    st.session_state["tab_key"] = "tab_key_0"

# initializing "tab at first round
if st.session_state["tab_key"] not in st.session_state:
    st.session_state[st.session_state["tab_key"]] = "Overview"

sac.buttons(
    [sac.ButtonsItem(label=i, icon=tabs_icons.get(i, None)) for i in tabs],
    index=tabs.index(st.session_state[st.session_state["tab_key"]]),
    format_func="title",
    align="center",
    key=st.session_state["tab_key"],
)
st.divider()
# create sidebar:
make_sidebar(api)

if st.session_state[st.session_state["tab_key"]] == "Info":
    st.text("Blue PtX Info")

if st.session_state[st.session_state["tab_key"]] == "Overview":
    st.text("Shows boths costs and emissions at a glance.")

if st.session_state[st.session_state["tab_key"]] == "Costs":
    st.text("Blue PtX Costs")

if st.session_state[st.session_state["tab_key"]] == "Emissions":
    st.markdown(
        """Bar charts showing emissions by source region, data
scenario and product chains

But more complex because of different ways to split emissions:
- By process step (like in _Costs_ tab)
- By GHG (CO2, CH4), or total (CO2 equivalents)
- Combustion vs fugitive emissions (leakages)
- Emitted vs captured
- Supply country vs demand country
"""
    )

if st.session_state[st.session_state["tab_key"]] == "Market scanning":
    st.text("Blue PtX Market scanning")


if st.session_state[st.session_state["tab_key"]] == "Input data":
    st.text("Blue PtX Input data")


if st.session_state[st.session_state["tab_key"]] == "Country fact sheets":
    st.text("Blue PtX Country fact sheets")


if st.session_state[st.session_state["tab_key"]] == "Certification schemes":
    st.text("Blue PtX Certification schemes")


if st.session_state[st.session_state["tab_key"]] == "Sustainability":
    st.text("Blue PtX Sustainability")


if st.session_state[st.session_state["tab_key"]] == "Literature":
    st.text("Blue PtX Literature")

display_footer()
