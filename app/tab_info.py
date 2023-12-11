# -*- coding: utf-8 -*-
"""Info tab."""
import streamlit as st


def content_info():
    with st.container(border=True):
        st.markdown("### What functionalities does this tool provide to users? ")
        st.markdown(
            """
    - Get an impression of **total costs of delivered hydrogen and various derivative
    molecules** of your country of interest to a potential demand country
    - Analyze the **cost components** of flexibly selectable process chains
    and production routes
    - **Compare costs** between various production pathways, supply and demand countries
    on a global scale
    - Access comprehensive **additional context information** on relevant aspects
    for PTX trade such as potential sustainability issues and certification
    - If required, **adjust data points** according to your own level of knowledge
    """,
            unsafe_allow_html=True,
        )

        st.markdown("### On the level of detail")
        st.markdown(
            """
    The tool calculates **simple levelized costs of hydrogen and derivatives**
    at screening/pre-feasbility level.
    The table below gives an overview on different levels
    of cost/price approximations.
    In this overview, the tool locates in first level which aims at providing
    high-level analyses at pre-feasibility level to start the discussion.
    It does not show realized project costs or hydrogen and derivative prices.

    """
        )
        st.image("static/costs_of_hydrogen.png", width=800)

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
        st.image("static/inout_header.png", width=800)
        st.image(f"static/inout_{step}.png", width=800)

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
        st.markdown("#### Disclaimer")
        st.markdown(
            """
        The PTX BOA uses technical reports published by third parties.
        The authors of the tool and Agora Energiewende trust but do not guarantee
        the accuracy and completeness of the information provided by them.

        All rights reserved to Öko-Institut and Agora Energiewende.
        The use of the methods and results are only authorised
        in case Öko-institut and Agora Energiewende is properly cited.
            """
        )

        st.markdown("#### Licensing and quotation")
        st.markdown(
            """
        This tool is licensed under the Creative Commons CC-BY-SA license
        (https://creativecommons.org/licenses/by-sa/4.0/).

        Please cite it as: Oeko-Institut, Agora Energiewende & Agora Industry (2023):
        PTX Business Opportunity Analyser
        https://ptx-boa.streamlit.app/
            """
        )
        st.markdown("#### Source code and contribution")
        st.markdown(
            """
        We strongly welcome anyone interested in contributing to this project.
        If you would like to file a bug, make a feature request
        or make a contribution, please check out our Github repository:
        https://github.com/agoenergy/ptx-boa
            """
        )

        st.markdown("#### Additional resources")
        st.markdown(
            """
        Visit our website for data documentation, additional resources and updates:
        https://www.agora-energiewende.de/en/publications/business-opportunity-analyser-boa
            """
        )

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
