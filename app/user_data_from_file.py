# -*- coding: utf-8 -*-
"""Functions for saving user data in a local file."""

import logging

import numpy as np
import pandas as pd
import streamlit as st

logger = logging.getLogger()


def upload_user_data(api):
    """Create a file upload and download interface."""
    if st.session_state["edit_input_data"]:
        # we use a file uploader key which is incremented in order to clear the
        # uploaded file
        # https://discuss.streamlit.io/t/are-there-any-ways-to-clear-file-uploader-values-without-using-streamlit-form/40903/2  # noqa
        if "file_uploader_key" not in st.session_state:
            st.session_state["file_uploader_key"] = 0
        if "upload_validation" not in st.session_state:
            st.session_state["upload_validation"] = None

        st.file_uploader(
            label="modified data file",
            type="csv",
            accept_multiple_files=False,
            help="Select modified data file downloaded from a previous session.",
            label_visibility="collapsed",
            on_change=upload_validation_callback,
            args=(api,),
            key=st.session_state["file_uploader_key"],
        )

        if isinstance(
            st.session_state["upload_validation"], pd.DataFrame
        ):  # validation passed
            st.success("Valid data file.")
            st.button(
                label="Apply Uploaded Data",
                on_click=apply_uploaded_user_data,
                type="primary",
            )
            if st.session_state["user_changes_df"] is not None:
                st.info(
                    "Applying data loaded from file will override your current changes."
                )

        if isinstance(
            st.session_state["upload_validation"], str
        ):  # string indicating error in validation
            msg = f"Uploaded data is not valid: {st.session_state['upload_validation']}"
            logger.info(f"Reject uploaded data: {msg}")
            c1, c2 = st.columns([0.9, 0.1])
            with c1:
                st.error(msg)
            with c2:
                st.button("OK", on_click=_empty_upload_validation)


def _empty_upload_validation():
    st.session_state["upload_validation"] = None


def upload_validation_callback(api) -> str | pd.DataFrame:
    """
    Validate the content of the file uploader.

    Used as a  "on_change" callback to the file uploader.

    Writes the result to "upload_validation" session_state variable:
        - if result is pd.DataFrame: all checks passed, file is valid
        - if result is str: Error, the string contains the error message.

    Also increments the file uploader key session state variable by 1, this creates a
    new file uploader and removes the already uploaded file.

    Checks:
        - correct column names.
        - numeric data in "value" column.
        - index combination present in input data.
        - correct ranges for certain parameters.

    Returns
    -------
    None
    """
    try:
        upload_key = st.session_state["file_uploader_key"]
        result = _read_user_data_file(st.session_state[upload_key])
    except Exception as e:  # noqa
        result = "csv parsing error"

    result = _validate_user_dataframe(
        api=api, scenario=st.session_state["scenario"], result=result
    )

    # cast empty strings to None in case validation passed
    if isinstance(result, pd.DataFrame):
        result = result.replace("", None)

    st.session_state["file_uploader_key"] += 1
    st.session_state["upload_validation"] = result


def _read_user_data_file(filehandle):
    return pd.read_csv(filehandle, keep_default_na=False, encoding="utf-8")


def _validate_user_dataframe(api, scenario, result: str | pd.DataFrame):
    # check for correct column names:
    if isinstance(result, pd.DataFrame):
        result = _validate_correct_column_names(result)

    # check that only numeric values are given in "value"
    if isinstance(result, pd.DataFrame):
        result = _validate_numeric_values(result)

    # check for correct index combinations:
    if isinstance(result, pd.DataFrame):
        result = _validate_correct_index_combinations(api, scenario, result)

    # check values are in correct ranges:
    if isinstance(result, pd.DataFrame):
        result = _validate_param_in_range(result)

    return result


def _validate_correct_index_combinations(api, scenario, result):
    # check that index-column combination is present in input data:
    input_data = api.get_input_data(scenario, long_names=True)
    for row in result.itertuples():
        selector = (
            (input_data["parameter_code"] == row.parameter_code)
            & (input_data["process_code"] == row.process_code)
            & (input_data["flow_code"] == row.flow_code)
            & (input_data["source_region_code"] == row.source_region_code)
            & (input_data["target_country_code"] == "")
        )
        if len(input_data.loc[selector]) == 0:
            result = (
                f"invalid index combination '{row.source_region_code} "
                f"| {row.process_code} | {row.parameter_code} | {row.flow_code}'"
            )
            break
    return result


def _validate_correct_column_names(result):
    required_cols = {
        "source_region_code",
        "process_code",
        "parameter_code",
        "flow_code",
        "value",
    }
    if set(result.columns) != required_cols:
        result = f"column names must be {sorted(required_cols)}"
    return result


def _validate_numeric_values(result):
    error = False
    values = result["value"].copy()
    try:
        values = values.astype(float)
        if values.isna().any():
            error = True
    except ValueError:
        # could not cast string to float
        error = True

    if error:
        result = "non numeric values in 'value' column."
    return result


def _validate_param_in_range(result):
    param_ranges = {  # entries are (lower_bound, upper_bound)
        "CAPEX": (0, np.inf),
        "OPEX (fix)": (0, np.inf),
        "efficiency": (0, 1),
        "lifetime / amortization period": (0, np.inf),
        "interest rate": (0, 1),
        "full load hours": (0, 8760),
        "specific costs": (0, np.inf),
        "losses (own fuel, transport)": (0, np.inf),
        "levelized costs": (0, np.inf),
    }
    for row in result.itertuples():
        p = row.parameter_code
        if p in param_ranges.keys():
            v = row.value
            if not param_ranges[p][0] <= v <= param_ranges[p][1]:
                result = (
                    f"'{p}' needs to be in range [{param_ranges[p][0]}, "
                    f"{param_ranges[p][1]}] but is {v}."
                )
                break
        else:
            logger.warning(f"range not checked for uploaded parameter '{p}'")

    return result


def download_user_data():
    """Dump the user changes from session state to a csv file."""
    data = (
        st.session_state["user_changes_df"]
        .fillna("")
        .to_csv(index=False, encoding="utf-8")
    )
    st.download_button(
        label="Download Modified Data",
        data=data,
        file_name="modified_ptxboa_data.csv",
        help="Click to download your current data modifications.",
        type="primary",
    )


def apply_uploaded_user_data():
    """Overwrite user changes in session state with uploaded data."""
    st.session_state["user_changes_df"] = st.session_state["upload_validation"]
    st.session_state["upload_validation"] = None
