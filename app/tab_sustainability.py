# -*- coding: utf-8 -*-
"""Content of sustainability tab."""
import streamlit as st

from app.ptxboa_functions import read_markdown_file


def _render_figure_and_introduction():
    st.image("static/sustainability.png")
    captiontext = (
        "Source: https://ptx-hub.org/wp-content/uploads/2022/05/"
        "PtX-Hub-PtX.Sustainability-Dimensions-and-Concerns-Scoping-Paper.pdf"
    )
    st.caption(captiontext)
    st.markdown(read_markdown_file("static/sustainability_intro.md"))


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
    with st.expander("What is this?"):
        st.markdown(
            """
**Get supplementary information on PTX-relevant sustainability issues**

Hydrogen is not sustainable by nature.
And sustainability goes far beyond the CO2-footprint of a product.
It also includes other environmental as well as socio-economic dimensions.

This is why we provide you with a set of questions that will help you assess your plans
for PTX production and export from a comprehensive sustainability perspective.
Please note that this list does not claim to be exhaustive,
but only serves for an orientation on the topic.
            """
        )

    st.markdown("## Dimensions of sustainability")
    with st.container(border=True):
        _render_figure_and_introduction()

    with st.container(border=True):
        _interactive_sustainability_dimension_info(context_data)
