# -*- coding: utf-8 -*-
"""Content of sustainability tab."""
import streamlit as st


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
    df = context_data["sustainability"]

    c1, c2 = st.columns([2, 1])
    with c1:
        st.image("static/sustainability.png")
        captiontext = (
            "Source: https://ptx-hub.org/wp-content/uploads/2022/05/"
            "PtX-Hub-PtX.Sustainability-Dimensions-and-Concerns-Scoping-Paper.pdf"
        )
        st.caption(captiontext)
    with c2:
        st.markdown(
            """
**Dimensions of sustainability**

**What sustainability aspects should be considered for PTX products,
 production and policies?**

**What questions should be asked before and during project development?**

In this tab we aim to provide a basic approach to these questions.
 To the left, you can see the framework along which the compilation
 of sustainability aspects in this tab is structured. It is based on the EESG framework
 as elaborated by the PtX Hub and sustainability criteria developed by the Öko-Institut.

**The framework distinguishes four key sustainability dimensions - Environmental,
 Economic, Social and Governance - from which you can select below.**

 Within each of these dimensions there are different clusters of sustainability aspects
 that we address in a set of questions. We differentiate between questions indicating
 guardrails and questions suggesting goals.

With this compilation, we aim to provide a general overview of the sustainability
 issues that may be relevant in the context of PTX production. Of course,
 different aspects are more or less important depending on the project,
 product and country.

**Take a look for yourself to see which dimensions are most important
 from where you are coming from.**
                    """
        )
    st.divider()

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
