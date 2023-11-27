# -*- coding: utf-8 -*-
"""Functions for saving user data in a local file."""

import pandas as pd
import streamlit as st


def upload_user_data(api):
    if st.session_state["edit_input_data"]:
        uploaded_file = st.file_uploader(
            label="modified data file",
            type="json",
            accept_multiple_files=False,
            help="Select modified data file downloaded from a previous session.",
            label_visibility="collapsed",
        )
        if uploaded_file is not None:
            validated = validate_uploaded_user_data(api, uploaded_file)
        else:
            validated = None

        if isinstance(validated, pd.DataFrame):
            if st.session_state["user_changes_df"] is not None:
                st.warning("Apply settings will override your current changes.")
            st.button(
                label="Apply Settings",
                on_click=apply_uploaded_user_data,
                args=(validated,),
            )

        if isinstance(validated, str):
            st.error(f"Uploaded data is not valid: {validated}")

        if not isinstance(validated, pd.DataFrame) or uploaded_file is None:
            st.warning("Select data to be uploaded.")


def validate_uploaded_user_data(api, uploaded_file):
    try:
        result = pd.read_json(uploaded_file, orient="records")
    except ValueError:
        return "json parsing error"

    if set(result.columns) != {
        "source_region_code",
        "process_code",
        "parameter_code",
        "value",
    }:
        return "wrong column names"

    # check that index column combination is present in input data:
    api.get_input_data(
        st.session_state["scenario"],
    )
    # TODO: validate records in result

    return result.replace("", None)


def download_user_data():
    data = (
        st.session_state["user_changes_df"]
        .fillna("")
        .to_json(orient="records", indent=2)
    )
    st.download_button(
        label="Download Modified Data",
        data=data,
        file_name="modified_ptxboa_data.json",
        help="Click to download your current data modifications.",
    )


def apply_uploaded_user_data(uploaded_df):
    st.session_state["user_changes_df"] = uploaded_df
