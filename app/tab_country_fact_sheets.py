# -*- coding: utf-8 -*-
"""Content of country fact sheets tab and functions to create it."""
import streamlit as st

from app.ptxboa_functions import get_region_from_subregion, read_markdown_file


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
            st.markdown(data["h2_demand_2030"])
            st.markdown(f"*Source: {data['source_h2_demand_2030']}*")
        with c2:
            st.markdown("**Targeted sectors (main):**")
            st.markdown(data["demand_targeted_sectors_main"])
            st.markdown(f"*Source: {data['source_targeted_sectors_main']}*")
        with c3:
            st.markdown("**Targeted sectors (secondary):**")
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

    if data["certification_info"] != "":
        with st.expander("**Certification schemes**"):
            st.markdown(data["certification_info"])
            st.markdown(f"*Source: {data['source_certification_info']}*")


def _create_fact_sheet_supply_country(context_data: dict):
    """Display information on a chosen supply country."""
    # select region:
    country_name = st.session_state["region"]

    # for subregions, select name of region they belong to:
    region_name = get_region_from_subregion(country_name)
    df = context_data["supply"]
    data = df.loc[df["country_name"] == region_name].iloc[0].to_dict()

    st.subheader(f"Fact sheet for {region_name}")
    with st.expander("**Technical potential for renewable electricity generation**"):
        text = (
            f"- {data['source_re_tech_pot_EWI']}: "
            f"\t{data['re_tech_pot_EWI']:.0f} TWh/a\n"
            f"- {data['source_re_tech_pot_PTXAtlas']}: "
            f"\t{data['re_tech_pot_PTXAtlas']:.0f} TWh/a\n"
        )
        st.markdown(text)

    with st.expander("**LNG infrastructure**"):
        text = (
            f"- {data['lng_export']} export terminals\n"
            f"- {data['lng_import']} import terminals.\n\n"
            f"*Source: {data['source_lng']}*"
        )
        st.markdown(text)

    st.write("TODO: CCS pot, elec prices, H2 strategy")


def content_country_fact_sheets(context_data):
    with st.expander("What is this?"):
        st.markdown(read_markdown_file("md/whatisthis_country_fact_sheets.md"))
    with st.container(border=True):
        _create_fact_sheet_demand_country(context_data)
    with st.container(border=True):
        _create_fact_sheet_supply_country(context_data)
