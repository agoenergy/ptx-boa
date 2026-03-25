# -*- coding: utf-8 -*-
"""
PtX BOA streamlit app, main file.

Execution:
>>> streamlit run  ptxboa_streamlit.py
"""

__version__ = "2.1.33"

import logging

import pandas as pd
import streamlit as st

from ptxboa_blue import blue_page
from ptxboa_green import green_page

# setup logging
# level can be changed on strartup with: --logger.level=LEVEL
loglevel = st.logger.get_logger(__name__).level
logger = logging.getLogger()  # do not use __name__ so we can resue it in submodules
logger.setLevel(loglevel)
if not logger.handlers:
    # only add one handler
    logger.handlers.append(logging.StreamHandler())
for handler in logger.handlers:
    handler.setFormatter(
        logging.Formatter(
            "[%(asctime)s %(levelname)7s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
    )

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)

# https://discuss.streamlit.io/t/can-not-set-page-width-in-streamlit-1-5-0/21522/5
css = """
<style>
    section.stMain > div {max-width:80rem}
</style>
"""
st.markdown(css, unsafe_allow_html=True)

# https://discuss.streamlit.io/t/delete-red-bar-at-the-top-of-the-app/9658
hide_decoration_bar_style = """
    <style>
        header {visibility: hidden;}
    </style>
"""
st.markdown(hide_decoration_bar_style, unsafe_allow_html=True)

page = st.navigation(
    [
        st.Page(
            green_page,
            default=True,
            title="Green PtX Business Opportunity Analyser",
        ),
        st.Page(
            blue_page,
            url_path="blue",
            title="Blue PtX Business Opportunity Analyser",
        ),
    ],
    position="hidden",
)

page.run()
