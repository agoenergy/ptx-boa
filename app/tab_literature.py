# -*- coding: utf-8 -*-
"""Content and halper functions for literature tab."""
from urllib.parse import urlparse

import streamlit as st

from app.ptxboa_functions import read_markdown_file


def _is_valid_url(url: str) -> bool:
    """Check if a string is a valid url."""
    if not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        # Check if result.scheme and result.netloc are non-empty
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def content_literature(context_data: dict):
    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_literature.md"))

    st.markdown("## References")
    df = context_data["literature"]
    markdown_text = ""
    for _ind, row in df.iterrows():
        if _is_valid_url(row["url"]):
            text = f"- {row['long_name'].strip('.')} ([Link]({row['url']}))\n"
        else:
            text = f"- {row['long_name']}\n"
        markdown_text = markdown_text + text

    st.markdown(markdown_text)
