# -*- coding: utf-8 -*-
"""Sidebar creation."""
import streamlit as st

from app.ptxboa_functions import reset_user_changes
from app.user_data_persistence import download_user_data, upload_user_data
from ptxboa.api import PtxboaAPI


def make_sidebar(api: PtxboaAPI):
    st.sidebar.subheader("Main settings:")
    if "include_subregions" not in st.session_state:
        st.session_state["include_subregions"] = False
    if st.session_state["include_subregions"]:
        region_list = api.get_dimension("region").index
    else:
        region_list = (
            api.get_dimension("region")
            .loc[api.get_dimension("region")["subregion_code"] == ""]
            .index
        )

    st.session_state["region"] = st.sidebar.selectbox(
        "Supply country / region:",
        region_list,
        help=(
            "One supply country or region can be selected here, "
            " and detailed settings can be selected for this region below "
            "(RE source, mode of transportation). For other regions, "
            "default settings will be used."
        ),
    )
    st.sidebar.toggle(
        "Include subregions",
        help=(
            "For three deep-dive countries (Argentina, Morocco, and South Africa) "
            "the app calculates costs for subregions as well. Activate this switch"
            "if you want to chose one of these subregions as a supply region. "
        ),
        key="include_subregions",
    )
    st.session_state["country"] = st.sidebar.selectbox(
        "Demand country:",
        api.get_dimension("country").index,
        help=(
            "The country you aim to export to. Some key info on the demand country you "
            "choose here are displayed in the info box."
        ),
    )
    # get chain as combination of product, electrolyzer type and reconversion option:
    c1, c2 = st.sidebar.columns(2)
    with c1:
        product = st.selectbox(
            "Product:",
            [
                "Ammonia",
                "Green Iron",
                "Hydrogen",
                "LOHC",
                "Methane",
                "Methanol",
                "Ft e-fuels",
            ],
            help="The product you want to export.",
        )
    with c2:
        ely = st.selectbox(
            "Electrolyzer type:",
            [
                "AEL",
                "PEM",
                "SEOC",
            ],
            help="The electrolyzer type you wish to use.",
        )
    if product in ["Ammonia", "Methane"]:
        use_reconversion = st.sidebar.toggle(
            "Include reconversion to H2",
            help=(
                "If activated, account for costs of "
                "reconverting product to H2 in demand country."
            ),
        )
    else:
        use_reconversion = False

    st.session_state["chain"] = f"{product} ({ely})"
    if use_reconversion:
        st.session_state["chain"] = f"{st.session_state['chain']} + reconv. to H2"

    st.session_state["res_gen"] = st.sidebar.selectbox(
        "Renewable electricity source (for selected supply region):",
        api.get_dimension("res_gen").index,
        help=(
            "The source of electricity for the selected source country. For all "
            "other countries Wind-PV hybrid systems will be used (an optimized mixture "
            "of PV and wind onshore plants)"
        ),
    )

    # get scenario as combination of year and cost assumption:
    c1, c2 = st.sidebar.columns(2)
    with c1:
        data_year = st.radio(
            "Data year:",
            [2030, 2040],
            index=1,
            help=(
                "To cover parameter uncertainty and development over time, we provide "
                "cost reduction pathways (high / medium / low) for 2030 and 2040."
            ),
            horizontal=True,
        )
    with c2:
        cost_scenario = st.radio(
            "Cost assumptions:",
            ["high", "medium", "low"],
            index=1,
            help=(
                "To cover parameter uncertainty and development over time, we provide "
                "cost reduction pathways (high / medium / low) for 2030 and 2040."
            ),
            horizontal=True,
        )
    st.session_state["scenario"] = f"{data_year} ({cost_scenario})"

    st.sidebar.subheader("Additional settings:")
    st.session_state["secproc_co2"] = st.sidebar.radio(
        "Carbon source:",
        api.get_dimension("secproc_co2").index,
        horizontal=True,
        help="Help text",
    )
    st.session_state["secproc_water"] = st.sidebar.radio(
        "Water source:",
        api.get_dimension("secproc_water").index,
        horizontal=True,
        help="Help text",
    )
    st.session_state["transport"] = st.sidebar.radio(
        "Mode of transportation (for selected supply country):",
        api.get_dimension("transport").index,
        horizontal=True,
        help="Help text",
    )
    if st.session_state["transport"] == "Ship":
        st.session_state["ship_own_fuel"] = st.sidebar.toggle(
            "For shipping option: Use the product as own fuel?",
            help="Help text",
        )
    st.session_state["output_unit"] = st.sidebar.radio(
        "Unit for delivered costs:",
        api.get_dimension("output_unit").index,
        horizontal=True,
        help="Help text",
    )

    st.sidebar.toggle(
        "Edit input data",
        help="""Activate this to enable editing of input data.
Currently, your changes will be stored, but they will not be
used in calculation and they will not be displayed in figures.

Disable this setting to reset user data to default values.""",
        value=False,
        key="edit_input_data",
        on_change=reset_user_changes,
    )

    with st.sidebar.container():
        if st.session_state["user_changes_df"] is not None:
            download_user_data()
        with st.expander(label="Reload Modified Data"):
            upload_user_data(api)

    return
