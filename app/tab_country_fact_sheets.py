# -*- coding: utf-8 -*-
"""Content of country fact sheets tab and functions to create it."""
import streamlit as st


def _create_fact_sheet_demand_country(context_data: dict):
    # select country:
    country_name = st.session_state["country"]
    with st.expander("What is this?"):
        st.markdown(
            """
**Country fact sheets**

This sheet provides you with additional information on the production and import of
 hydrogen and derivatives in all PTX BOA supply and demand countries.
For each selected supply and demand country pair, you will find detailed
 country profiles.

 For demand countries, we cover the following aspects:
 country-specific projected hydrogen demand,
 target sectors for hydrogen use,
 hydrogen-relevant policies and competent authorities,
 certification and regulatory frameworks,
 and country-specific characteristics as defined in the demand countries'
 hydrogen strategies.

 For the supplying countries, we cover the country-specific technical potential
 for renewables (based on various data sources),
 LNG export and import infrastructure,
 CCS potentials,
 availability of an H2 strategy
 and wholesale electricity prices.
            """
        )
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
    # select country:
    country_name = st.session_state["region"]
    df = context_data["supply"]
    data = df.loc[df["country_name"] == country_name].iloc[0].to_dict()

    st.subheader(f"Fact sheet for {country_name}")
    text = (
        "**Technical potential for renewable electricity generation:**\n"
        f"- {data['source_re_tech_pot_EWI']}: "
        f"\t{data['re_tech_pot_EWI']:.0f} TWh/a\n"
        f"- {data['source_re_tech_pot_PTXAtlas']}: "
        f"\t{data['re_tech_pot_PTXAtlas']:.0f} TWh/a\n"
    )

    st.markdown(text)

    text = (
        "**LNG infrastructure:**\n"
        f"- {data['lng_export']} export terminals\n"
        f"- {data['lng_import']} import terminals.\n\n"
        f"*Source: {data['source_lng']}*"
    )

    st.markdown(text)

    st.write("TODO: CCS pot, elec prices, H2 strategy")


def content_country_fact_sheets(context_data):
    _create_fact_sheet_demand_country(context_data)
    st.divider()
    _create_fact_sheet_supply_country(context_data)
