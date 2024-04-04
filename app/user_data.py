# -*- coding: utf-8 -*-
"""Functions related to user modified input data in frontend."""
import numpy as np
import pandas as pd
import streamlit as st


def register_user_changes(
    missing_index_name: str,
    missing_index_value: str,
    index: str,
    columns: str,
    values: str,
    df_tab: pd.DataFrame,
    df_orig: pd.DataFrame,
    key: str,
    editor_key: str,
):
    """
    Register all user changes in the session state variable "user_changes_df".

    If a change already has been recorded, use the lastest value.
    """
    # convert session state dict to dataframe:
    # Create a list of dictionaries
    data_dict = st.session_state[editor_key]["edited_rows"]
    if any(data_dict.values()):
        data_list = []

        rejected_changes = False
        for k, v in data_dict.items():
            for c_name, value in v.items():
                if np.isnan(df_orig.iloc[k, :][c_name]):
                    msg = (
                        f":exclamation: Cannot modify empty value '{c_name}' "
                        f"for '{df_orig.index[k]}'"
                    )
                    st.toast(msg)
                    rejected_changes = True
                else:
                    data_list.append({index: k, columns: c_name, values: value})

        if rejected_changes:
            # modify key number
            st.session_state[f"{key}_number"] += 1

        if len(data_list) == 0:
            return

        # Convert the list to a DataFrame
        res = pd.DataFrame(data_list)

        # add missing key (the info that is not contained in the 2D table):
        if missing_index_name is not None or missing_index_value is not None:
            res[missing_index_name] = missing_index_value

        # Replace the 'id' values with the corresponding index elements from df_tab
        res[index] = res[index].map(lambda x: df_tab.index[x])

        # convert the interest rate from [%] to [decimals]
        res["value"] = res["value"].astype(float)
        res.loc[res["parameter_code"] == "interest rate", "value"] = (
            res.loc[res["parameter_code"] == "interest rate", "value"] / 100
        )

        if st.session_state["user_changes_df"] is None:
            st.session_state["user_changes_df"] = pd.DataFrame(
                columns=[
                    "source_region_code",
                    "process_code",
                    "parameter_code",
                    "flow_code",
                    "value",
                ]
            )

        # only track the last changes if a duplicate entry is found.
        st.session_state["user_changes_df"] = pd.concat(
            [st.session_state["user_changes_df"].astype(res.dtypes), res]
        ).drop_duplicates(
            subset=[
                "source_region_code",
                "process_code",
                "parameter_code",
                "flow_code",
            ],
            keep="last",
        )


def reset_user_changes():
    """Reset all user changes."""
    if (
        not st.session_state["edit_input_data"]
        and st.session_state["user_changes_df"] is not None
    ):
        st.session_state["user_changes_df"] = None


def display_user_changes(api):
    """Display input data changes made by user."""
    if st.session_state["user_changes_df"] is not None:
        df = st.session_state["user_changes_df"].copy()

        # convert the interest rate from [decimals] to [%]
        df.loc[df["parameter_code"] == "interest rate", "value"] = (
            df.loc[df["parameter_code"] == "interest rate", "value"] * 100
        )

        parameters = api.get_dimension("parameter")
        df["Unit"] = df["parameter_code"].map(
            pd.Series(parameters["unit"].tolist(), index=parameters["parameter_name"])
        )
        st.dataframe(
            df.rename(
                columns={
                    "source_region_code": "Source Region",
                    "process_code": "Process",
                    "parameter_code": "Parameter",
                    "flow_code": "Carrier/Material",
                    "value": "Value",
                }
            ).style.format(precision=3),
            hide_index=True,
        )
    else:
        st.write("You have not changed any values yet.")
