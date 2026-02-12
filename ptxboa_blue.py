"""Content of blue Ptx subpage."""

import streamlit as st
import streamlit_antd_components as sac

from app.layout_elements import display_footer
from app.sidebar import make_sidebar_blue
from app.tab_blue_costs import content_costs
from app.tab_blue_costs_comparison import content_costs_comparison
from app.tab_blue_emissions import content_emissions
from app.user_data import display_user_changes
from app.user_data_from_file import download_user_data, upload_user_data
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
if "user_changes_df" not in st.session_state:
    st.session_state["user_changes_df"] = None

if "edit_input_data" not in st.session_state:
    st.session_state["edit_input_data"] = False

st.title("Blue PtX Business Opportunity Analyser")

with st.container():
    if st.session_state["edit_input_data"]:
        st.info("Data editing mode **ON**")
        with st.expander("Modified data"):
            if st.session_state["user_changes_df"] is not None:
                download_user_data()
            display_user_changes(api)

            with st.container():
                st.divider()
                st.markdown("##### Upload your data from a previous session")
                upload_user_data(api)
    else:
        placeholder = st.empty()

tabs = (
    "Info",
    "Costs",
    "Emissions",
    "Input data",
    "Costs Comparison",
)

tabs_icons = {
    "Costs": "house-fill",
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
    st.session_state[st.session_state["tab_key"]] = "Costs"

sac.buttons(
    [sac.ButtonsItem(label=i, icon=tabs_icons.get(i, None)) for i in tabs],
    index=tabs.index(st.session_state[st.session_state["tab_key"]]),
    format_func="title",
    align="center",
    key=st.session_state["tab_key"],
)
st.divider()
# create sidebar:
make_sidebar_blue(api)

# DUMMIES:
st.session_state["chain"] = "Ammonia (AEL)"
st.session_state["scenario"] = "2040 (medium)"
st.session_state["secproc_water"] = "Specific costs"
st.session_state["subregion"] = None
st.session_state["output_product"] = "Ammonia"

if st.session_state[st.session_state["tab_key"]] == "Info":
    st.text("Blue PtX Info")

if st.session_state[st.session_state["tab_key"]] == "Costs":
    content_costs(api)

if st.session_state[st.session_state["tab_key"]] == "Costs Comparison":
    content_costs_comparison(api)

if st.session_state[st.session_state["tab_key"]] == "Emissions":
    content_emissions(api)

if st.session_state[st.session_state["tab_key"]] == "Input data":
    st.text("Blue PtX Input data")

display_footer()
