# -*- coding: utf-8 -*-
"""Content of sustainability tab."""
import streamlit as st

from app.ptxboa_functions import read_markdown_file


def _render_figure_and_introduction():
    st.image("img/sustainability.png")
    captiontext = (
        "Source: [PtX HUB (2022)](https://ptx-hub.org/wp-content/uploads/2022/05/"
        "PtX-Hub-PtX.Sustainability-Dimensions-and-Concerns-Scoping-Paper.pdf)"
    )
    st.caption(captiontext)
    st.markdown(
        read_markdown_file("md/sustainability_intro.md"), unsafe_allow_html=True
    )


def _interactive_sustainability_dimension_info(context_data: dict):
    df = context_data["sustainability"]
    c1, c2 = st.columns(2)
    with c1:
        helptext = "helptext"
        dimension = st.selectbox(
            "Select dimension:", df["dimension"].unique(), help=helptext
        )
    with c2:
        helptext = """
We understand **guardrails** as guidelines which can help you to produce green
PTX products that are sustainable also beyond their greenhouse gas emission intensity.

**Goals** are guidelines which can help link PTX production to improving local
ecological and socio-economic circumstances in the supply country.
They act as additional to guardrails which should be fulfilled in the first place
to meet basic sustainability needs.
"""
        question_type = st.radio(
            "Guardrails or goals?",
            ["Guardrails", "Goals"],
            help=helptext,
            horizontal=True,
        )
        data = df.loc[(df["dimension"] == dimension) & (df["type"] == question_type)]

    for topic in data["topic"].unique():
        with st.expander(f"**{topic}**"):
            data_select = data.loc[data["topic"] == topic]
            for _ind, row in data_select.iterrows():
                st.markdown(f"- {row['question']}")


def content_sustainability(context_data: dict):
    with st.popover("*Help*", use_container_width=True):
        st.markdown(
            read_markdown_file("md/whatisthis_sustainability.md"),
            unsafe_allow_html=True,
        )

    st.markdown("## Dimensions of sustainability")
    with st.container(border=True):
        _render_figure_and_introduction()

    with st.container(border=True):
        _interactive_sustainability_dimension_info(context_data)
