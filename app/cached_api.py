"""Single place where streamlit initalizes PtxboaAPI as cached resource."""

import streamlit as st

from ptxboa import DEFAULT_CACHE_DIR, DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI

api = st.cache_resource(PtxboaAPI)(
    data_dir=DEFAULT_DATA_DIR,
    cache_dir=DEFAULT_CACHE_DIR,
)
