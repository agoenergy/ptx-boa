# -*- coding: utf-8 -*-
"""Info tab."""
import streamlit as st

from app.ptxboa_functions import read_markdown_file

__version__ = "2.0.2"


def content_info():
    with st.container(border=True):
        st.markdown(read_markdown_file("md/info_intro.md"), unsafe_allow_html=True)

        st.image("img/costs_of_hydrogen.png", width=800)

    with st.container(border=True):
        st.markdown(
            "### What's in | What's out in the tool's calculations and assumptions?"
        )

        step = st.radio(
            "Select process step:",
            [
                "General",
                "Electricity generation",
                "Electrolysis",
                "Derivative production",
                "Transport",
            ],
            horizontal=True,
        )
        st.image("img/inout_header.png", width=800)
        st.image(f"img/inout_{step.replace(' ', '_').lower()}.png", width=800)

        st.markdown(
            """
    Note that this overview is not comprehensive in the sense that it shows
      all assumptions at a glance.
    Rather, the issues listed are aspects that have emerged in discussions
      with stakeholders (deep-dive country workshops) prior to the publication
        of the tool and which we believe require detailed explanation.
    """
        )

    with st.container(border=True):
        st.markdown(read_markdown_file("md/info_disclaimer.md"), unsafe_allow_html=True)
        st.markdown(
            (
                "#### Licensing and quotation\n"
                "This tool is licensed under the Creative Commons CC-BY 4.0 license"
                " (<https://creativecommons.org/licenses/by/4.0/>).\n\n"
                "The use of the methods and results are only authorised"
                " in case the tool and its authors are properly cited.\n\n"
                "Please cite it as:"
                " Oeko-Institut, Agora Industry & Agora Energiewende  (2024):"
                f" PTX Business Opportunity Analyser {__version__}"
                " <https://www.agora-industry.org/data-tools/ptx-business-opportunity-analyser>)"  # noqa
            )
        )
