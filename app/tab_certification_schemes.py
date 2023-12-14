# -*- coding: utf-8 -*-
"""Content of certification schemes tab."""
import numpy as np
import streamlit as st

from app.ptxboa_functions import read_markdown_file


def _render_scheme_info(context_data, scheme_name):
    df = context_data["certification_schemes"]
    data_with_na = df.loc[df["name"] == scheme_name].iloc[0].to_dict()

    # replace na with "not specified"
    data = {}  # never modify a dict when iterating over it.
    for key, value in data_with_na.items():
        if value in ["", " ", np.nan]:
            data[key] = "not specified"
        else:
            data[key] = value

    st.markdown(data["description"])

    with st.expander("**Characteristics**"):
        st.markdown(
            (
                f"- **Relation to other schemes, standards or regulations:** "
                f"{data['relation_to_other_standards']}"
            )
        )
        st.markdown(
            (
                f"- **Demand countries where this scheme, standard or regulation "
                f"applies:** {data['ptxboa_demand_countries']}"
            )
        )
        st.markdown(f"- **Labels:** {data['label']}")
        st.markdown(f"- **Lifecycle scope:** {data['lifecycle_scope']}")

        st.markdown(
            """
**Explanations**

- Info on "Lifecycle scope":
  - Well-to-gate: GHG emissions are calculated up to production.
  - Well-to-wheel: GHG emissions are calculated up to the time of use.
  - Further information on the life cycle scopes can be found in
IRENA & RMI (2023): Creating a global hydrogen market: certification to enable trade,
 pp. 15-19
"""
        )

    with st.expander("**Scope**"):
        if data["scope_emissions"] != "not specified":
            st.markdown("- **Emissions**")
            st.markdown(data["scope_emissions"])

        if data["scope_electricity"] != "not specified":
            st.markdown("- **Electricity**")
            st.markdown(data["scope_electricity"])

        if data["scope_water"] != "not specified":
            st.markdown("- **Water**")
            st.markdown(data["scope_water"])

        if data["scope_biodiversity"] != "not specified":
            st.markdown("- **Biodiversity**")
            st.markdown(data["scope_biodiversity"])

        if data["scope_other"] != "not specified":
            st.markdown("- **Other**")
            st.markdown(data["scope_other"])

    with st.expander("**Sources**"):
        st.markdown(data["sources"])


def content_certification_schemes(context_data: dict):
    with st.expander("What is this?"):
        st.markdown(read_markdown_file("md/whatisthis_certification_schemes.md"))

    helptext = "Select the certification scheme you want to know more about."
    scheme_name = st.selectbox(
        "Select scheme:", context_data["certification_schemes"]["name"], help=helptext
    )
    with st.container(border=True):
        _render_scheme_info(context_data=context_data, scheme_name=scheme_name)
