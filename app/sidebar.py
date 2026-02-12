# -*- coding: utf-8 -*-
"""Sidebar creation."""

import streamlit as st

from app.ptxboa_functions import read_markdown_file
from app.user_data import reset_user_changes
from ptxboa.api import PtxboaAPI


def make_sidebar_green(api: PtxboaAPI):
    logo_section()
    with main_settings_expander():
        main_settings_green(api)
    with additional_settings_expander():
        additional_settings_green(api)
    st.sidebar.divider()
    edit_input_data_toggle()
    input_data_reset_notice()


def make_sidebar_blue(api: PtxboaAPI):
    logo_section()
    with main_settings_expander():
        main_settings_blue(api)
    with additional_settings_expander():
        additional_settings_blue(api)
    st.sidebar.divider()
    edit_input_data_toggle()
    input_data_reset_notice()


def main_settings_green(api: PtxboaAPI):
    # get list of regions that does not contain subregions:
    region_list = (
        api.get_dimension("region", tool_version_color="green")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .sort_index()
        .index
    )

    # select region:
    region = st.selectbox(
        "Supply country / region:",
        region_list,
        help=(read_markdown_file("md/helptext_sidebar_green_supply_region.md")),
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
    countries = api.get_dimension("country", tool_version_color="green").index
    st.session_state["country"] = st.selectbox(
        "Demand country:",
        countries,
        help=read_markdown_file("md/helptext_sidebar_green_demand_country.md"),
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
            "Include reconversion to H₂",
            help=(
                read_markdown_file("md/helptext_sidebar_include_reconversion_to_h2.md")
            ),
        )
    else:
        use_reconversion = False

    st.session_state["chain"] = f"{product} ({st.session_state['electrolyzer']})"
    if use_reconversion:
        st.session_state["chain"] = f"{st.session_state['chain']} + reconv. to H2"

    available_res_gen = sorted(api.get_res_technologies(st.session_state["region"]))
    st.session_state["res_gen"] = st.selectbox(
        "Renewable electricity source (only for selected supply region, other regions use Wind-PV hybrid):",  # noqaCO2 source
        available_res_gen,
        index=available_res_gen.index("Wind-PV-Hybrid"),
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


def main_settings_blue(api: PtxboaAPI):
    regions = (
        api.get_dimension("region", tool_version_color="blue")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .sort_index()
        .index.to_list()
    )

    # select region:
    st.selectbox(
        "Supply country:",
        regions,
        help=read_markdown_file("md/helptext_sidebar_blue_supply_region.md"),
        index=regions.index("Morocco"),  # Morocco as default
        key="region",
    )

    countries = api.get_dimension("country", tool_version_color="blue").index.to_list()
    st.selectbox(
        "Demand country:",
        countries,
        help=read_markdown_file("md/helptext_sidebar_blue_demand_country.md"),
        index=countries.index("Germany"),
        key="country",
    )

    production_location = st.radio(
        "Where does production take place:",
        ["supply", "demand"],
        horizontal=True,
        format_func=lambda x: {
            "supply": "Supply Country",
            "demand": "Demand Country",
        }.get(x, x),
        help=read_markdown_file("md/helptext_sidebar_blue_ptx_production_country.md"),
    )

    product = st.selectbox(
        label="Final Product:",
        options=[
            "NH3-L",
            "CHX-L",
            "DRI-S",
            "H2-G",
            "CH3OH-L",
        ],
        format_func=lambda x: {
            "CHX-L": "FT e-fuels",
            "DRI-S": "Green iron",
            "NH3-L": "Ammonia",
            "H2-G": "Hydrogen",
            "CH3OH-L": "Methanol",
        }.get(x, x),
        help=read_markdown_file("md/helptext_sidebar_product.md"),
        index=0,
    )

    conversion_options = [
        "ATR_91%",
        "SMR_52%",
        "SMR_52%_BF",
    ]

    if product == "CH3OH-L":
        conversion_options.append("CH3OHSYC")
    if product == "CHX-L":
        conversion_options.append("EFUELSYNC")
    if product == "DRI-S":
        conversion_options.append("NG-DRI-C")

    conversion = st.selectbox(
        label="Conversion:",
        options=conversion_options,
        format_func=lambda x: {
            "ATR_91%": "ATR",
            "SMR_52%": "SMR",
            "SMR_52%_BF": "SMR Brownfield",
        }.get(x, x),
        help=read_markdown_file("md/helptext_sidebar_blue_conversion.md"),
        index=0,
    )

    if product == "H2-G" and production_location == "supply":
        nh3_transport = st.toggle(
            "Transport NH₃ and reconvert to H₂",
            value=False,
            help=read_markdown_file(
                "md/helptext_sidebar_blue_transport_NH3_and_reconvert_to_H2.md"
            ),
        )
    else:
        nh3_transport = False

    # build chain:
    chain = f"{product}__{conversion}__prod_in_{production_location}"
    if nh3_transport:
        chain += "__transport_NH3-L"

    st.session_state["chain"] = chain

    # scenario is combination of year and cost assumption
    # for blue PtxBoa, we only use medium cost assumption
    data_year = st.radio(
        "Data year:",
        [2030, 2040],
        index=1,
        help=read_markdown_file("md/helptext_sidebar_blue_data-year.md"),
        horizontal=True,
    )
    cost_scenario = "medium"
    st.session_state["scenario"] = f"{data_year} ({cost_scenario})"


def additional_settings_green(api):
    co2_source_toggle(api)
    water_source_radio(api)
    allow_pipeline_toggle()
    ship_own_fuel_toggle()
    unit_toggle_green()


def additional_settings_blue(api: PtxboaAPI):
    co2_source_toggle(api)
    allow_pipeline_toggle()
    ship_own_fuel_toggle()
    unit_toggle_blue()


@st.cache_resource()
def sidebar_logo():
    st.image("img/Agora_Industry_logo_612x306.png")


def logo_section():
    st.logo(
        image="img/transparent_10x10.png",  # placeholder when sidebar is expanded
        icon_image="img/Agora_Industry_logo_612x306.png",
    )
    with st.sidebar:
        sidebar_logo()


def main_settings_expander():
    return st.sidebar.expander("**Main settings**", expanded=True)


def additional_settings_expander():
    return st.sidebar.expander("**Additional settings**", expanded=False)


def edit_input_data_toggle():
    st.sidebar.toggle(
        "Edit input data",
        help=read_markdown_file("md/helptext_sidebar_edit_input_data.md"),
        value=False,
        key="edit_input_data",
        on_change=reset_user_changes,
    )


def input_data_reset_notice():
    if (
        st.session_state["edit_input_data"]
        and st.session_state["user_changes_df"] is not None
    ):
        st.sidebar.info("Modified data is reset when turned **OFF**")


def water_source_radio(api: PtxboaAPI):
    st.session_state["secproc_water"] = st.radio(
        "Water source:",
        api.get_dimension("secproc_water").index,
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_water_source.md"),
    )


def co2_source_toggle(api: PtxboaAPI):
    st.session_state["secproc_co2"] = st.radio(
        "CO₂ source:",
        api.get_dimension("secproc_co2").index,
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_carbon_source.md"),
    )


def ship_own_fuel_toggle():
    st.session_state["ship_own_fuel"] = st.toggle(
        "For shipping option: Use the product as own fuel?",
        help=read_markdown_file("md/helptext_sidebar_transport_use_own_fuel.md"),
    )


def unit_toggle_green():
    st.session_state["output_unit"] = st.radio(
        "Unit for delivered costs:",
        ["USD/MWh", "USD/t"],
        horizontal=True,
        help=read_markdown_file("md/helptext_sidebar_cost_unit.md"),
        index=1,  # 'USD/t' as default
    )


def unit_toggle_blue():
    st.session_state["output_unit"] = st.radio(
        "Unit per cost and emissions:",
        ["USD/MWh", "USD/t"],
        horizontal=True,
        format_func=lambda x: {
            "USD/MWh": "per MWh final product",
            "USD/t": "per tonne final product",
        }.get(x, x),
        help=read_markdown_file("md/helptext_sidebar_blue_cost_unit.md"),
        index=1,  # 'per/t' as default
    )
    st.session_state["emissions_output_unit"] = st.session_state["output_unit"].replace(
        "USD", "gCO₂eq"
    )


def allow_pipeline_toggle():
    allow_pipeline = st.toggle(
        "Allow pipeline transport",
        help=read_markdown_file("md/helptext_sidebar_transport.md"),
        value=True,
    )
    if allow_pipeline:
        st.session_state["transport"] = "Pipeline"
    else:
        st.session_state["transport"] = "Ship"
