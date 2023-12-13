# -*- coding: utf-8 -*-
"""Utility functions to download a pd.DataFrame as Excel file with streamlit."""
from io import BytesIO

import pandas as pd
import streamlit as st

st.cache_data()


def prepare_df_as_excel_stream(df: pd.DataFrame) -> bytes:
    """
    Convert a Dataframe to excel bytes stream.

    Parameters
    ----------
    df : pd.DataFrame
        _description_

    Returns
    -------
    pd.DataFrame
        _description_
    """
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine="xlsxwriter")
    df.to_excel(writer, index=True, sheet_name="Data")
    writer.close()
    return output.getvalue()


def prepare_and_download_df_as_excel(df: pd.DataFrame, filename: str):
    """
    Prepare a bytes stream and add streamlit download button.

    https://stackoverflow.com/a/70120061

    Parameters
    ----------
    df : pd:dataFrame
    filename : str
        filename will be appended with ".xlsx"

    Returns
    -------
    None
    """
    excel_stream = prepare_df_as_excel_stream(df)

    st.download_button(
        label="Download Table as Excel",
        data=excel_stream,
        file_name=f"{filename}.xlsx",
        help="Click to download this Table as Excel File.",
    )
    return None
