# -*- coding: utf-8 -*-
"""Content of country fact sheets tab and functions to create it."""
import streamlit as st

from app.ptxboa_functions import get_region_from_subregion, read_markdown_file
from ptxboa.api import PtxboaAPI


def _create_fact_sheet_demand_country(context_data: dict):
    # select country:
    country_name = st.session_state["country"]
    df = context_data["demand_countries"]
    data = df.loc[df["country_name"] == country_name].iloc[0].to_dict()

    flags_to_country_names = {
        "France": ":flag-fr:",
        "Germany": ":flag-de:",
        "Netherlands": ":flag-nl:",
        "Spain": ":flag-es:",
        "China": ":flag-cn:",
        "India": ":flag-in:",
        "Japan": ":flag-jp:",
        "South Korea": ":flag-kr:",
        "USA": ":flag-us:",
    }

    st.subheader(
        f"{flags_to_country_names[country_name]} Fact sheet for {country_name}"
    )
    with st.expander("**Demand**"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Projected H2 demand in 2030:**")
            if data["h2_demand_2030"] in ["", "-", "n/a"]:
                st.markdown("no data")
            else:
                st.markdown(data["h2_demand_2030"])
                st.markdown(f"*Source: {data['source_h2_demand_2030']}*")
        with c2:
            st.markdown("**Targeted sectors (main):**")
            if data["demand_targeted_sectors_main"] in ["", "-", "n/a"]:
                st.markdown("no data")
            else:
                st.markdown(data["demand_targeted_sectors_main"])
                st.markdown(f"*Source: {data['source_targeted_sectors_main']}*")
        with c3:
            st.markdown("**Targeted sectors (secondary):**")
            if data["demand_targeted_sectors_secondary"] in [
                "",
                "-",
                "n/a",
                " ",
            ]:
                st.markdown("no data")
            else:
                st.markdown(data["demand_targeted_sectors_secondary"])
                st.markdown(f"*Source: {data['source_targeted_sectors_secondary']}*")

    with st.expander("**Hydrogen strategy**"):
        st.markdown("**Documents:**")
        st.markdown(data["h2_strategy_documents"])

        st.markdown("**Authorities:**")
        st.markdown(data["h2_strategy_authorities"])

    with st.expander("**Hydrogen trade characteristics**"):
        st.markdown(data["h2_trade_characteristics"])
        st.markdown(f"*Source: {data['source_h2_trade_characteristics']}*")

    with st.expander("**Infrastructure**"):
        st.markdown("**LNG import terminals:**")
        st.markdown(data["lng_import_terminals"])
        st.markdown(f"*Source: {data['source_lng_import_terminals']}*")

        st.markdown("**H2 pipeline projects:**")
        st.markdown(data["h2_pipeline_projects"])
        st.markdown(f"*Source: {data['source_h2_pipeline_projects']}*")

    if (
        len(data["certification_info"]) > 1
    ):  # workaround, empty data sometimes contains "-"
        with st.expander("**Certification schemes**"):
            st.markdown(data["certification_info"])
            st.markdown(f"*Source: {data['source_certification_info']}*")


def _create_fact_sheet_supply_country(context_data: dict, api: PtxboaAPI):
    """Display information on a chosen supply country."""
    alpha2_codes = api.get_dimension("region")["iso3166_code"].to_dict()

    # select region:
    country_name = st.session_state["region"]

    # for subregions, select name of region they belong to:
    region_name = get_region_from_subregion(country_name)
    df = context_data["supply"]
    data = df.loc[df["country_name"] == region_name].iloc[0].to_dict()

    flag = f":flag-{alpha2_codes[region_name]}:".lower()

    st.subheader(f"{flag} Fact sheet for {region_name}")
    with st.expander("**Technical potential for renewable electricity generation**"):
        if isinstance(data["re_tech_pot_EWI"], (int, float)):
            re_tech_pot_EWI = f"{data['re_tech_pot_EWI']:.0f} TWh/a"
        else:
            re_tech_pot_EWI = data["re_tech_pot_EWI"]

        if isinstance(data["re_tech_pot_PTXAtlas"], (int, float)):
            re_tech_pot_PTXAtlas = f"{data['re_tech_pot_PTXAtlas']:.0f} TWh/a"
        else:
            re_tech_pot_PTXAtlas = data["re_tech_pot_PTXAtlas"]

        text = (
            f"- {data['source_re_tech_pot_EWI']}: \t{re_tech_pot_EWI}\n"
            f"- {data['source_re_tech_pot_PTXAtlas']}: \t{re_tech_pot_PTXAtlas}\n"
        )
        st.markdown(text)

    with st.expander("**LNG infrastructure**"):
        text = (
            f"- {data['lng_export']} export terminals\n"
            f"- {data['lng_import']} import terminals\n\n"
            f"*Source: {data['source_lng']}*"
        )
        st.markdown(text)

    with st.expander("**Carbon Capture & Storage (CCS) Potentials**"):
        value = data["ccs_pot"]
        source = data["source_ccs1"]
        if value == "n/a":
            st.markdown("no data")
        else:
            st.markdown(f"**{value}**\n\n*Source: {source}*")

    with st.expander("**Electricity Prices**"):
        value = data["elec_prices_IEA2020"]
        source = data["source_elec_prices"]
        if value == "n/a":
            st.markdown("no data")
        else:
            st.markdown(f"{value:.2f} USD/MWh\n\n*Source: {source}*")

    with st.expander(
        "**Is there already a hydrogen strategy existing or in planning?**"
    ):
        st.markdown(data["h2_strategy"])


def content_country_fact_sheets(context_data, api):
    with st.expander("What is this?"):
        st.markdown(read_markdown_file("md/whatisthis_country_fact_sheets.md"))
    with st.container(border=True):
        _create_fact_sheet_demand_country(context_data)
    with st.container(border=True):
        _create_fact_sheet_supply_country(context_data, api)
