# -*- coding: utf-8 -*-
"""Sidebar creation."""
import streamlit as st

from app.ptxboa_functions import read_markdown_file
from app.user_data import reset_user_changes
from ptxboa.api import PtxboaAPI


@st.cache_resource()
def sidebar_logo():
    st.image("img/Agora_Industry_logo_612x306.png")


def make_sidebar(api: PtxboaAPI):
    st.logo(
        image="img/transparent_10x10.png",  # placeholder when sidebar is expanded
        icon_image="img/Agora_Industry_logo_612x306.png",
    )

    with st.sidebar:
        sidebar_logo()

    with st.sidebar.expander("**Main settings**", expanded=True):
        main_settings(api)

    with st.sidebar.expander("**Additional settings**", expanded=False):
        additional_settings(api)

    st.sidebar.divider()

    st.sidebar.toggle(
        "Edit input data",
        help=read_markdown_file("md/helptext_sidebar_edit_input_data.md"),
        value=False,
        key="edit_input_data",
        on_change=reset_user_changes,
    )
    if (
        st.session_state["edit_input_data"]
        and st.session_state["user_changes_df"] is not None
    ):
        st.sidebar.info("Modified data is reset when turned **OFF**")

    return


def main_settings(api):
    # get list of regions that does not contain subregions:
    region_list = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .sort_index()
        .index
    )

    # select region:
    region = st.selectbox(
        "Supply country / region:",
        region_list,
        help=(read_markdown_file("md/helptext_sidebar_supply_region.md")),
        index=region_list.get_loc("Morocco"),  # Morocco as default
    )
    st.session_state["region"] = region
    st.session_state["subregion"] = None

    # If a deep dive country has been selected, add option to select subregion:
    if region in ["Argentina", "Morocco", "South Africa"]:
        subregions = api.get_dimension("region")["region_name"]
        subregions = subregions.loc[
            (subregions.str.startswith(region)) & (subregions != region)
        ]
        subregion = st.selectbox(
            "Select subregion:",
            subregions,
            index=None,
            help=(read_markdown_file("md/helptext_sidebar_supply_subregion.md")),
        )
        if subregion is not None:
            st.session_state["region"] = subregion
            st.session_state["subregion"] = subregion

    # select demand country:
    countries = api.get_dimension("country").index
    st.session_state["country"] = st.selectbox(
        "Demand country:",
        countries,
        help=read_markdown_file("md/helptext_sidebar_demand_country.md"),
        index=countries.get_loc("Germany"),
    )
    # get chain as combination of product, electrolyzer type and reconversion option:
    c1, c2 = st.columns(2)
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
                "FT e-fuels",
            ],
            help=read_markdown_file("md/helptext_sidebar_product.md"),
            index=0,  # Ammonia as default
        )
    with c2:
        st.session_state["electrolyzer"] = st.selectbox(
            "Electrolyzer type:",
            [
                "AEL",
                "PEM",
                "SOEC",
            ],
            help=read_markdown_file("md/helptext_sidebar_electrolyzer_type.md"),
            index=0,  # AEL as default
        )
    if product in ["Ammonia", "Methane"]:
        use_reconversion = st.toggle(
            "Include reconversion to H2",
            help=(
                read_markdown_file("md/helptext_sidebar_include_reconversion_to_h2.md")
            ),
        )
    else:
        use_reconversion = False

    st.session_state["chain"] = f"{product} ({st.session_state['electrolyzer']})"
    if use_reconversion:
        st.session_state["chain"] = f"{st.session_state['chain']} + reconv. to H2"

    available_res_gen = api.get_res_technologies(st.session_state["region"])
    st.session_state["res_gen"] = st.selectbox(
        "Renewable electricity source (for selected supply region):",
        available_res_gen,
        index=available_res_gen.index("PV tilted"),
        help=read_markdown_file("md/helptext_sidebar_re_source.md"),
    )

    # get scenario as combination of year and cost assumption:
    c1, c2 = st.columns(2)
    with c1:
        data_year = st.radio(
            "Data year:",
            [2030, 2040],
            index=1,
            help=read_markdown_file("md/helptext_sidebar_data-year.md"),
            horizontal=True,
        )
    with c2:
        cost_scenario = st.radio(
            "Cost assumptions:",
            ["high", "medium", "low"],
            index=1,
            help=read_markdown_file("md/helptext_sidebar_cost_assumptions.md"),
            horizontal=True,
        )
    st.session_state["scenario"] = f"{data_year} ({cost_scenario})"


def additional_settings(api):
    st.session_state["secproc_co2"] = st.radio(
        "CO2 source:",
        api.get_dimension("secproc_co2").index,
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_carbon_source.md"),
    )

    st.session_state["secproc_water"] = st.radio(
        "Water source:",
        api.get_dimension("secproc_water").index,
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_water_source.md"),
    )

    # determine transportation distance, only allow pipeline if <6000km:
    res = api.get_input_data(st.session_state["scenario"])
    distance = res.loc[
        (res["source_region_code"] == st.session_state["region"])
        & (res["target_country_code"] == st.session_state["country"])
        & (res["parameter_code"] == "shipping distance"),
        "value",
    ].iloc[0]

    if distance < 6000:
        st.session_state["transport"] = st.radio(
            "Mode of transportation (for selected supply country):",
            ["Ship", "Pipeline"],
            horizontal=True,
            help=read_markdown_file("md/helptext_sidebar_transport.md"),
            index=1,  # 'Pipeline' as default
        )
    else:
        st.session_state["transport"] = st.radio(
            "Mode of transportation (for selected supply country):",
            ["Ship", "Pipeline"],
            horizontal=True,
            help=read_markdown_file("md/helptext_sidebar_transport.md"),
            index=0,  # select 'ship' and disable widget
            disabled=True,
        )
    if st.session_state["transport"] == "Ship":
        st.session_state["ship_own_fuel"] = st.toggle(
            "For shipping option: Use the product as own fuel?",
            help=read_markdown_file("md/helptext_sidebar_transport_use_own_fuel.md"),
        )
    else:
        st.session_state["ship_own_fuel"] = False

    st.session_state["output_unit"] = st.radio(
        "Unit for delivered costs:",
        ["USD/MWh", "USD/t"],
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_cost_unit.md"),
        index=1,  # 'USD/t' as default
    )
