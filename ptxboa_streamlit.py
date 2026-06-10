# -*- coding: utf-8 -*-
"""
PtX BOA streamlit app, main file.

Execution:
>>> streamlit run  ptxboa_streamlit.py
"""

import logging

import pandas as pd
import streamlit as st

# load api into cache once
from app.cached_api import api  # noqa: F401
from ptxboa_blue import content_blue_page
from ptxboa_green import content_green_page

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

st.logo(
    image="img/transparent_10x10.png",  # placeholder when sidebar is expanded
    icon_image="img/Agora_Industry_logo_612x306.png",
)


green_page = st.Page(
    content_green_page,
    url_path="ptx",
    title="PtX Business Opportunity Analyser",
)

blue_page = st.Page(
    content_blue_page,
    url_path="lowcarbon",
    title="Low-Carbon Business Opportunity Analyser",
)


def content_landing_page():
    st.set_page_config(page_icon="./data/favicon-16x16.png")
    cols = st.columns([0.5, 1, 1, 0.5])
    with cols[1]:
        st.page_link(
            green_page,
            label="PtX Business Opportunity Analyser",
        )
    with cols[2]:
        st.page_link(
            blue_page,
            label="Low-Carbon Business Opportunity Analyser",
        )


page = st.navigation(
    [
        st.Page(
            content_landing_page,
            default=True,
            title="PtX Business Opportunity Analyser",
        ),
        green_page,
        blue_page,
    ],
    position="hidden",
)

page.run()
