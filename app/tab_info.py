# -*- coding: utf-8 -*-
"""Info tab."""
import streamlit as st

from app.ptxboa_functions import read_markdown_file


def content_info():
    with st.container(border=True):
        st.markdown(read_markdown_file("md/info_intro.md"))

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
                "Derivate production",
                "Transport",
            ],
            horizontal=True,
        )
        st.image("img/inout_header.png", width=800)
        st.image(f"img/inout_{step}.png", width=800)

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
        st.markdown(read_markdown_file("md/info_disclaimer.md"))

    with st.container(border=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                """
                ##### Developed by:
                Öko-Institut<br/>
                Merzhauser Straße 173<br/>
                D-79100 Freiburg im Breisgau<br/>
                www.oeko.de
                """,
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                """
                ##### On behalf of:
                Agora Energiewende<br/>
                Anna-Louisa-Karsch-Str. 2<br/>
                D-10178 Berlin<br/>
                www.agora-energiewende.de
                """,
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                """
                ##### Authors:
                - Christoph Heinemann
                - Dr. Roman Mendelevitch
                - Markus Haller
                - Christian Winger
                - Johannes Aschauer
                - Susanne Krieger
                - Katharina Göckeler
                """,
                unsafe_allow_html=True,
            )
