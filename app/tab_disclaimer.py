# -*- coding: utf-8 -*-
"""Info tab."""
import streamlit as st


def content_info():
    with st.expander("What is this?"):
        st.markdown(
            """
**Info**

Information on product details of the PTX Business Opportunity Analyser
 including a citation suggestion of the tool.
            """
        )
    st.image("static/info.png")
    st.image("static/info_2.png")
