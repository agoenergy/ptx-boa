"""Blue info tab."""

import streamlit as st

from app.layout_elements import report_processes_contained_in_process_result_type
from app.ptxboa_functions import read_markdown_file
from ptxboa.api import PtxboaAPI


def content_info(api: PtxboaAPI):
    with st.container(border=True):
        st.markdown(read_markdown_file("md/tab_blue_info/blue_info.md"))

        report_processes_contained_in_process_result_type(api, "blue")
