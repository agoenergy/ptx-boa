"""Content of green Ptx subpage."""

from datetime import date

import streamlit as st
import streamlit_antd_components as sac

from app.cached_api import api
from app.context_data import load_context_data
from app.layout_elements import display_footer
from app.ptxboa_functions import read_markdown_file
from app.sidebar import make_sidebar_green
from app.tab_debugging import content_debugging
from app.tab_green_certification_schemes import content_certification_schemes
from app.tab_green_costs import content_costs
from app.tab_green_country_fact_sheets import content_country_fact_sheets
from app.tab_green_deep_dive_countries import content_deep_dive_countries
from app.tab_green_info import content_info
from app.tab_green_input_data import content_input_data
from app.tab_green_literature import content_literature
from app.tab_green_market_scanning import content_market_scanning
from app.tab_green_optimization import content_optimization
from app.tab_green_sustainability import content_sustainability
from app.user_data import display_user_changes
from app.user_data_from_file import download_user_data, upload_user_data
from app.utils import get_app_mode
from ptxboa import __version__

MODE = get_app_mode()


@st.cache_data()
def update_note(current_date: date):
    valid_until = date(year=2026, month=9, day=1)
    if current_date < valid_until:
        with st.expander(
            "June 2026: Updated Version! Click here for more information.", icon="📣"
        ):
            st.markdown(read_markdown_file("md/green_update_note_june_2026.md"))


def content_green_page():
    st.set_page_config(
        page_icon="./data/favicon-16x16.png",
    )

    if "model_status" not in st.session_state:
        st.session_state["model_status"] = "not yet solved"

    if "user_changes_df" not in st.session_state:
        st.session_state["user_changes_df"] = None

    if "edit_input_data" not in st.session_state:
        st.session_state["edit_input_data"] = False

    st.title("PtX Business Opportunity Analyser")
    st.markdown(f"_Version {__version__}_")

    update_note(date.today())

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
            _placeholder = st.empty()  # noqa F841

    tabs = (
        "Info",
        "Costs",
        "Market scanning",
        "Deep-dive countries",
        "Optimization",
        "Input data",
        "Country fact sheets",
        "Certification schemes",
        "Sustainability",
        "Literature",
    )
    if MODE in {"dev", "preview"}:
        tabs = tabs + ("Debugging",)

    tabs_icons = {
        "Costs": "house-fill",
        "Info": "question-circle-fill",
    }

    # the "tab_key" is used to identify the sac.tabs element. Whenever a tab is switched
    # programatically (e.g. via app.ptxboa.functions.move_to_tab), "tab_key" entry is
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
    make_sidebar_green(api)

    if st.session_state[st.session_state["tab_key"]] in [
        "Market scanning",
        "Deep-dive countries",
        "Country fact sheets",
        "Certification schemes",
        "Sustainability",
        "Literature",
    ]:
        # import context data:
        cd = load_context_data()

    # costs:
    if st.session_state[st.session_state["tab_key"]] == "Costs":
        content_costs(api)

    if st.session_state[st.session_state["tab_key"]] == "Market scanning":
        content_market_scanning(api, cd)

    if st.session_state[st.session_state["tab_key"]] == "Input data":
        content_input_data(api)

    if st.session_state[st.session_state["tab_key"]] == "Deep-dive countries":
        content_deep_dive_countries(api)

    if st.session_state[st.session_state["tab_key"]] == "Country fact sheets":
        content_country_fact_sheets(cd, api)

    if st.session_state[st.session_state["tab_key"]] == "Certification schemes":
        content_certification_schemes(cd)

    if st.session_state[st.session_state["tab_key"]] == "Sustainability":
        content_sustainability(cd)

    if st.session_state[st.session_state["tab_key"]] == "Literature":
        content_literature(cd)

    if st.session_state[st.session_state["tab_key"]] == "Info":
        content_info()

    if st.session_state[st.session_state["tab_key"]] == "Optimization":
        content_optimization(api)

    if st.session_state[st.session_state["tab_key"]] == "Debugging":
        content_debugging(api, tool_version_color="green")

    display_footer(tool_version_color="green")
