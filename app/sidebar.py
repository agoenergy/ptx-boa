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
    edit_input_data_toggle_green()
    input_data_reset_notice()


def make_sidebar_blue(api: PtxboaAPI):
    logo_section()
    with main_settings_expander():
        main_settings_blue(api)
    with additional_settings_expander():
        additional_settings_blue(api)
    st.sidebar.divider()
    edit_input_data_toggle_blue()
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
        help=(read_markdown_file("md/sidebar/helptext_sidebar_green_supply_region.md")),
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
            help=(
                read_markdown_file("md/sidebar/helptext_sidebar_supply_subregion.md")
            ),
        )
        if subregion is not None:
            st.session_state["region"] = subregion
            st.session_state["subregion"] = subregion

    # select demand country:
    countries = api.get_dimension("country", tool_version_color="green").index
    st.session_state["country"] = st.selectbox(
        "Demand country:",
        countries,
        help=read_markdown_file("md/sidebar/helptext_sidebar_green_demand_country.md"),
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
            help=read_markdown_file("md/sidebar/helptext_sidebar_product.md"),
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
            help=read_markdown_file("md/sidebar/helptext_sidebar_electrolyzer_type.md"),
            index=0,  # AEL as default
        )
    if (
        product in ["Ammonia", "Methane"]
        # reconversion is not working if the demand country is equal to supply country
        # see https://github.com/agoenergy/ptx-boa/issues/615
        and st.session_state["region"] != st.session_state["country"]
    ):
        use_reconversion = st.toggle(
            "Include reconversion to H₂",
            help=(
                read_markdown_file(
                    "md/sidebar/helptext_sidebar_include_reconversion_to_h2.md"
                )
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
        help=read_markdown_file("md/sidebar/helptext_sidebar_re_source.md"),
    )

    # get scenario as combination of year and cost assumption:
    c1, c2 = st.columns(2)
    with c1:
        data_year = st.radio(
            "Data year:",
            [2030, 2040],
            index=1,
            help=read_markdown_file("md/sidebar/helptext_sidebar_data-year.md"),
            horizontal=True,
        )
    with c2:
        cost_scenario = st.radio(
            "Cost assumptions:",
            ["high", "medium", "low"],
            index=1,
            help=read_markdown_file("md/sidebar/helptext_sidebar_cost_assumptions.md"),
            horizontal=True,
        )
    st.session_state["scenario"] = f"{data_year} ({cost_scenario})"


def main_settings_blue(api: PtxboaAPI):
    NO_LNG_EXPORT = {"Brazil", "China", "India", "Thailand"}
    regions = (
        api.get_dimension("region", tool_version_color="blue")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .sort_index()
        .index.to_list()
    )

    # select region:
    region = st.selectbox(
        "Supply country (origin of natural gas)",
        regions,
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_supply_region.md"),
        index=regions.index("Algeria"),  # Morocco not implemented in blue
        key="region",
    )

    if region in NO_LNG_EXPORT:
        countries = [region]
        st.info(f"{region} does not export natural gas.")
    else:
        countries = api.get_dimension(
            "country", tool_version_color="blue"
        ).index.to_list()

    st.selectbox(
        "Demand country",
        countries,
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_demand_country.md"),
        index=0 if region in NO_LNG_EXPORT else countries.index("Germany"),
        disabled=region in NO_LNG_EXPORT,
        key="country",
    )

    if st.session_state["region"] != st.session_state["country"]:
        conversion_location = conversion_location_radio(
            key="conversion_location_radio", disabled=False
        )
    else:
        # necessary to make a new st.radio to reset selected value to "supply"
        conversion_location = conversion_location_radio(
            key="conversion_location_radio_disabled", disabled=True
        )

    st.session_state["conversion_location"] = conversion_location

    product_labels = {
        "CHX-L": "FT e-fuels",
        "B-DRI-S": "Iron",
        "STL-S": "Crude steel",
        "NH3-L": "Ammonia",
        "H2-G": "Hydrogen",
        "CH3OH-L": "Methanol",
    }

    product_groups = {
        "NH3-L": ["NH3-L", "CHX-L", "H2-G", "CH3OH-L"],
        "CHX-L": ["NH3-L", "CHX-L", "H2-G", "CH3OH-L"],
        "H2-G": ["NH3-L", "CHX-L", "H2-G", "CH3OH-L"],
        "CH3OH-L": ["NH3-L", "CHX-L", "H2-G", "CH3OH-L"],
        "STL-S": ["STL-S", "B-DRI-S"],
        "B-DRI-S": ["STL-S", "B-DRI-S"],
    }

    product_options = ["H2-G", "NH3-L", "CHX-L", "CH3OH-L", "STL-S", "B-DRI-S"]

    product = st.selectbox(
        label="Final Product",
        options=product_options,
        format_func=lambda x: product_labels.get(x, x),
        help=read_markdown_file("md/sidebar/helptext_sidebar_product.md"),
        index=0,
        key="output_product",
    )

    # add product label to session state
    st.session_state["output_product_label"] = product_labels.get(product, product)
    st.session_state["output_product_group"] = product_groups.get(
        product, product_options
    )

    # different conversion options for each product
    conversion_options = {
        "H2-G": [
            "ATR_91%",
            "SMR_52%",
            "SMR_52%_BF",
        ],
        "NH3-L": [
            "ATR_91%_NH3SYN",
            "SMR_52%_NH3SYN",
            "SMR_52%_BF_NH3SYN",
        ],
        "CH3OH-L": [
            "CH3OHSYC",
            "ATR_91%_CH3OHSYN",
            "SMR_52%_CH3OHSYN",
            "SMR_52%_BF_CH3OHSYN",
        ],
        "CHX-L": [
            "EFUELSYNC",
            "ATR_91%_EFUELSYN",
            "SMR_52%_EFUELSYN",
            "SMR_52%_BF_EFUELSYN",
        ],
        "STL-S": [
            "NG-DRI-C_EAF",
            "ATR_91%_DRI_EAF",
            "SMR_52%_DRI_EAF",
            "SMR_52%_BF_DRI_EAF",
            "ATR_91%_DRI-rotary_EAF",
            "SMR_52%_DRI-rotary_EAF",
            "SMR_52%_BF_DRI-rotary_EAF",
        ],
        "B-DRI-S": [
            "NG-DRI-C",
            "ATR_91%_DRI",
            "SMR_52%_DRI",
            "SMR_52%_BF_DRI",
            "ATR_91%_DRI-rotary",
            "SMR_52%_DRI-rotary",
            "SMR_52%_BF_DRI-rotary",
        ],
    }

    conversion = st.selectbox(
        label="Conversion route from natural gas",
        options=conversion_options[product],
        format_func=lambda x: {
            "ATR_91%": "H₂ (ATR)",
            "SMR_52%": "H₂ (SMR)",
            "SMR_52%_BF": "H₂ (brownfield SMR)",
            "ATR_91%_NH3SYN": "H₂ (ATR) | ammonia synthesis (Haber-Bosch)",
            "SMR_52%_NH3SYN": "H₂ (SMR) | ammonia synthesis (Haber-Bosch)",
            "SMR_52%_BF_NH3SYN": "H₂ (brownfield SMR) | ammonia synthesis (Haber-Bosch)",  # noqa E501
            "ATR_91%_CH3OHSYN": "H₂ (ATR) | methanol synthesis",
            "SMR_52%_CH3OHSYN": "H₂ (SMR) | methanol synthesis",
            "SMR_52%_BF_CH3OHSYN": "H₂ (brownfield SMR) | methanol synthesis",
            "CH3OHSYC": "natural gas-based methanol synthesis (current standard route)",
            "ATR_91%_EFUELSYN": "H₂ (ATR) | efuel synthesis (Fischer-Tropsch)",
            "SMR_52%_EFUELSYN": "H₂ (SMR) | efuel synthesis (Fischer-Tropsch)",
            "SMR_52%_BF_EFUELSYN": "H₂ (brownfield SMR) | efuel synthesis (Fischer-Tropsch)",  # noqa E501
            "EFUELSYNC": "natural gas-based efuel synthesis (GtL)",
            "ATR_91%_DRI_EAF": "H₂ (ATR) | shaft furnace (DRI) | steel making (EAF)",
            "SMR_52%_DRI_EAF": "H₂ (SMR) | shaft furnace (DRI) | steel making (EAF)",
            "SMR_52%_BF_DRI_EAF": "H₂ (brownfield SMR) | shaft furnace (DRI) | steel making (EAF)",  # noqa E501
            "ATR_91%_DRI-rotary_EAF": "H₂ (ATR) | rotary kiln (DRI) | steel making (EAF)",  # noqa E501
            "SMR_52%_DRI-rotary_EAF": "H₂ (SMR) | rotary kiln (DRI) | steel making (EAF)",  # noqa E501
            "SMR_52%_BF_DRI-rotary_EAF": "H₂ (brownfield SMR) | rotary kiln (DRI) | steel making (EAF)",  # noqa E501
            "NG-DRI-C_EAF": "natural gas | shaft furnace (DRI) | steel making (EAF)",
            "ATR_91%_DRI": "H₂ (ATR) | shaft furnace (DRI)",
            "SMR_52%_DRI": "H₂ (SMR) | shaft furnace (DRI)",
            "SMR_52%_BF_DRI": "H₂ (brownfield SMR) | shaft furnace (DRI)",
            "NG-DRI-C": "natural gas | shaft furnace (DRI)",
            "ATR_91%_DRI-rotary": "H₂ (ATR) | rotary kiln (DRI)",
            "SMR_52%_DRI-rotary": "H₂ (SMR) | rotary kiln (DRI)",
            "SMR_52%_BF_DRI-rotary": "H₂ (brownfield SMR) | rotary kiln (DRI)",
        }.get(x, x),
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_conversion.md"),
        index=0,
    )

    def get_reformer(conversion: str):
        if conversion.startswith("SMR_52%_BF"):
            return "SMR_52%_BF#B"
        if conversion.startswith("SMR_52%"):
            return "SMR_52%#B"
        if conversion.startswith("ATR_91%"):
            return "ATR_91%#B"
        return None

    st.session_state["reformer"] = get_reformer(conversion)

    if (
        product == "H2-G"
        and conversion_location == "supply"
        and st.session_state["region"] != st.session_state["country"]
    ):
        nh3_transport = st.toggle(
            "Transport ammonia and reconvert to hydrogen",
            value=False,
            help=read_markdown_file(
                "md/sidebar/helptext_sidebar_blue_transport_NH3_and_reconvert_to_H2.md"
            ),
        )
    else:
        nh3_transport = False

    # build chain:
    chain = f"{product}__{conversion}__prod_in_{conversion_location}"
    if nh3_transport:
        chain += "__transport_NH3-L"

    st.session_state["chain"] = chain

    # scenario is combination of year and cost assumption
    # for blue PtxBoa, we only use medium cost assumption
    data_year = st.radio(
        "Data year",
        [2030, 2040],
        index=0,
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_data-year.md"),
        horizontal=True,
    )
    cost_scenario = "medium"
    st.session_state["scenario"] = f"{data_year} ({cost_scenario})"


def conversion_location_radio(key: str, disabled: bool):
    return st.radio(
        "Where does conversion from natural gas to the final product take place?",
        ["supply", "demand"],
        index=0,
        horizontal=True,
        format_func=lambda x: {
            "supply": "Supply Country",
            "demand": "Demand Country",
        }.get(x, x),
        help=read_markdown_file(
            "md/sidebar/helptext_sidebar_blue_ptx_production_country.md"
        ),
        key=key,
        disabled=disabled,
    )


def additional_settings_green(api):
    co2_source_toggle_green()
    water_source_radio(api)
    allow_pipeline_toggle(default_value=True)
    ship_own_fuel_toggle("For shipping option: Use the product as own fuel?")
    unit_toggle_green()


def additional_settings_blue(api: PtxboaAPI):
    final_use_emissions_toggle()
    co2_source_toggle_blue()
    allow_pipeline_toggle(default_value=False)
    ship_own_fuel_toggle("For shipping option: Use the final product as own fuel?")
    unit_toggle_blue()


@st.cache_resource()
def sidebar_logo():
    st.image("img/Agora_Industry_logo_612x306.png")


def logo_section():
    with st.sidebar:
        sidebar_logo()


def main_settings_expander():
    return st.sidebar.expander("**Main settings**", expanded=True)


def additional_settings_expander():
    return st.sidebar.expander("**Additional settings**", expanded=False)


def edit_input_data_toggle_green():
    st.sidebar.toggle(
        "Edit input data",
        help=read_markdown_file("md/sidebar/helptext_sidebar_edit_input_data.md"),
        value=False,
        key="edit_input_data",
        on_change=reset_user_changes,
    )


def edit_input_data_toggle_blue():
    st.sidebar.toggle(
        "Edit input data (e.g. natural gas price)",
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_edit_input_data.md"),
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
        help=read_markdown_file("md/sidebar/helptext_sidebar_water_source.md"),
    )


def final_use_emissions_toggle():
    include_final_use = st.toggle(
        "Include emissions from final use",
        value=True,
        help=read_markdown_file(
            "md/sidebar/helptext_sidebar_blue_final_use_emissions.md"
        ),
    )
    st.session_state["emissions_included"] = (
        "upstream_and_final_use" if include_final_use else "upstream"
    )


def co2_source_toggle_green():
    st.session_state["secproc_co2"] = st.radio(
        "CO₂ source:",
        ["Direct Air Capture", "Specific costs"],
        horizontal=True,
        help=read_markdown_file("md/sidebar/helptext_sidebar_carbon_source.md"),
    )


def co2_source_toggle_blue():
    co2_source = st.radio(
        "CO₂ source:",
        ["Direct Air Capture (blue)", "industrial_capture"],
        format_func=lambda x: {
            "industrial_capture": "captured  CO₂ from industrial process",
            "Direct Air Capture (blue)": "Direct Air Capture",
        }.get(x, x),
        horizontal=True,
        help=read_markdown_file("md/sidebar/helptext_sidebar_blue_carbon_source.md"),
    )

    if co2_source == "industrial_capture":
        co2_source = st.radio(
            "Type of industrial CO₂ source:",
            [
                "CO2 from hard-to-abate or sustainable sources",
                "CO2 from other industrial sources",
            ],
            format_func=lambda x: {
                "CO2 from other industrial sources": "CO₂ from other industrial sources",  # noqa: E501
                "CO2 from hard-to-abate or sustainable sources": "CO₂ from hard-to-abate or sustainable sources",  # noqa: E501
            }.get(x, x),
            horizontal=True,
            help=read_markdown_file(
                "md/sidebar/helptext_sidebar_blue_industrial_co2_accounting.md"
            ),
        )

    if co2_source not in [
        "Direct Air Capture (blue)",
        "CO2 from other industrial sources",
        "CO2 from hard-to-abate or sustainable sources",
    ]:
        raise ValueError(f"invalid {co2_source=}")

    st.session_state["secproc_co2"] = co2_source


def ship_own_fuel_toggle(label: str):
    st.session_state["ship_own_fuel"] = st.toggle(
        label=label,
        help=read_markdown_file(
            "md/sidebar/helptext_sidebar_transport_use_own_fuel.md"
        ),
    )


def unit_toggle_green():
    st.session_state["output_unit"] = st.radio(
        "Unit for delivered costs:",
        ["USD/MWh", "USD/t"],
        horizontal=True,
        help=read_markdown_file("md/sidebar/helptext_sidebar_cost_unit.md"),
        index=1,  # 'USD/t' as default
    )


def unit_toggle_blue():
    def _radio(key: str, disabled: bool):
        return st.radio(
            "Unit for costs:",
            ["USD/MWh", "USD/t"],
            horizontal=True,
            format_func=lambda x: {
                "USD/MWh": "per MWh (LHV) final product",
                "USD/t": "per tonne final product",
            }.get(x, x),
            help=read_markdown_file("md/sidebar/helptext_sidebar_blue_cost_unit.md"),
            index=1,  # 'per/t' as default
            key=key,
            disabled=disabled,
        )

    if st.session_state["output_product"] in ["STL-S", "B-DRI-S"]:
        unit = _radio("_blue_unit_disabled", disabled=True)
    else:
        unit = _radio("_blue_unit", disabled=False)

    st.session_state["output_unit"] = unit

    st.session_state["emissions_output_unit"] = (
        st.session_state["output_unit"].replace("USD", "gCO₂eq").replace("MWh", "GJ")
    )


def allow_pipeline_toggle(default_value: bool):
    allow_pipeline = st.toggle(
        "Allow pipeline transport",
        help=read_markdown_file("md/sidebar/helptext_sidebar_transport.md"),
        value=default_value,
    )
    if allow_pipeline:
        st.session_state["transport"] = "Pipeline"
    else:
        st.session_state["transport"] = "Ship"
