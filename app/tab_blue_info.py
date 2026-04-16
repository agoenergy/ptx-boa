"""Blue info tab."""

import streamlit as st

from app.layout_elements import report_processes_contained_in_process_result_type
from ptxboa.api import PtxboaAPI


def content_info(api: PtxboaAPI):
    st.text("Blue PtX Info")
    report_processes_contained_in_process_result_type(api, "blue")
