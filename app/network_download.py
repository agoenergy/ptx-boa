# -*- coding: utf-8 -*-
"""Utility functions to download a pypsa network as netcdf file with streamlit."""
import os
import tempfile

import pypsa
import streamlit as st


def save_network(n: pypsa.Network) -> str:
    """Write pypsa network to temporary file."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".nc") as tmp:
        n.export_to_netcdf(
            path=tmp.name, export_standard_types=False, compression=None, float32=False
        )
        return tmp.name


def download_network_as_netcdf(n: pypsa.Network, filename: str) -> None:
    """Create button for downloading a pypsa network as netcdf file."""
    if st.button("Prepare Network for Download"):
        filename_tmp = save_network(n)
        with open(filename_tmp, "rb") as f:
            b = f.read()
            st.download_button(
                label="Download Network as NetCDF",
                data=b,
                file_name=filename,
                mime="application/x-netcdf",
            )
        os.remove(filename_tmp)  # clean up temporary file
