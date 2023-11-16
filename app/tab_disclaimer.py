# -*- coding: utf-8 -*-
"""Disclaimer tab."""
import streamlit as st


def content_disclaimer():
    with st.expander("What is this?"):
        st.markdown(
            """
**Disclaimer**

Information on product details of the PTX Business Opportunity Analyser
 including a citation suggestion of the tool.
            """
        )
    st.image("static/disclaimer.png")
    st.image("static/disclaimer_2.png")
