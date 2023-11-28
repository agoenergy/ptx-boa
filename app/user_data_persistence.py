# -*- coding: utf-8 -*-
"""Functions for saving user data in a local file."""

import pandas as pd
import streamlit as st


def upload_user_data(api):
    if st.session_state["edit_input_data"]:
        if "file_uploader_key" not in st.session_state:
            st.session_state["file_uploader_key"] = 0

        uploaded_file = st.file_uploader(
            label="modified data file",
            type="csv",
            accept_multiple_files=False,
            help="Select modified data file downloaded from a previous session.",
            label_visibility="collapsed",
            key=st.session_state["file_uploader_key"],
        )
        if uploaded_file is not None:
            validated = validate_uploaded_user_data(api, uploaded_file)
        else:
            validated = None

        if isinstance(validated, pd.DataFrame):
            st.success("Valid data file.")
            if st.session_state["user_changes_df"] is not None:
                st.warning(
                    "Applying data loaded from file will override your current changes."
                )
            st.button(
                label="Apply uploaded data",
                on_click=apply_uploaded_user_data,
                args=(validated,),
            )

        if isinstance(validated, str):
            st.error(f"Uploaded data is not valid: {validated}")

        if not isinstance(validated, pd.DataFrame) or uploaded_file is None:
            st.warning("Select data file to be uploaded.")


def validate_uploaded_user_data(api, uploaded_file):
    try:
        result = pd.read_csv(uploaded_file, keep_default_na=False)
    except:  # noqa
        return "csv parsing error"

    if set(result.columns) != {
        "source_region_code",
        "process_code",
        "parameter_code",
        "value",
    }:
        return "wrong column names"

    # check that index column combination is present in input data:
    input_data = api.get_input_data(st.session_state["scenario"], long_names=True)
    for row in result.itertuples():
        selector = (
            (input_data["parameter_code"] == row.parameter_code)
            & (input_data["process_code"] == row.process_code)
            & (input_data["flow_code"] == "")
            & (input_data["source_region_code"] == row.source_region_code)
            & (input_data["target_country_code"] == "")
        )
        if len(input_data.loc[selector]) == 0:
            return (
                f"invalid index combination '{row.source_region_code} "
                f"| {row.process_code} | {row.parameter_code}'"
            )

    return result.replace("", None)


def download_user_data():
    data = st.session_state["user_changes_df"].fillna("").to_csv(index=False)
    st.download_button(
        label="Download Modified Data",
        data=data,
        file_name="modified_ptxboa_data.csv",
        help="Click to download your current data modifications.",
    )


def apply_uploaded_user_data(uploaded_df):
    st.session_state["user_changes_df"] = uploaded_df
    st.session_state["file_uploader_key"] += 1
