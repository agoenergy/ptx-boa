# -*- coding: utf-8 -*-
"""Content of input data tab."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.plot_functions import plot_costs_on_map
from app.ptxboa_functions import display_and_edit_data_table
from ptxboa.api import PtxboaAPI


def content_deep_dive_countries(api: PtxboaAPI, res_costs: pd.DataFrame) -> None:
    """Create content for the "costs by region" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Deep-dive countries: Data on country and regional level**

For the three deep-dive countries (Argentina, Morocco and South Africa)
this tab shows full load hours of renewable generation and total costs
in regional details.

The box plots show median, 1st and 3rd quartile as well as the total spread of values.
They also show the data for your selected supply country or region for comparison.
            """
        )

    ddc = st.radio(
        "Select country:", ["Argentina", "Morocco", "South Africa"], horizontal=True
    )

    fig_map = plot_costs_on_map(api, res_costs, scope=ddc, cost_component="Total")
    st.plotly_chart(fig_map, use_container_width=True)

    # get input data:

    input_data = api.get_input_data(st.session_state["scenario"])

    # filter data:
    # get list of subregions:
    region_list = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["region_name"].str.startswith(ddc)]
        .index.to_list()
    )

    # TODO: implement display of total costs
    list_data_types = ["full load hours"]
    data_selection = st.radio(
        "Select data type",
        list_data_types,
        horizontal=True,
        key="sel_data_ddc",
    )
    if data_selection == "full load hours":
        parameter_code = ["full load hours"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        x = "process_code"
        missing_index_name = "parameter_code"
        missing_index_value = "full load hours"
        column_config = {"format": "%.0f h/a", "min_value": 0, "max_value": 8760}

    if data_selection == "total costs":
        df = res_costs.copy()
        df = res_costs.loc[region_list].rename({"Total": data_selection}, axis=1)
        df = df.rename_axis("source_region_code", axis=0)
        x = None
        st.markdown("TODO: fix surplus countries in data table")

    c1, c2 = st.columns(2, gap="medium")
    with c2:
        # show data:
        st.markdown("**Data:**")
        df = display_and_edit_data_table(
            input_data=input_data,
            missing_index_name=missing_index_name,
            missing_index_value=missing_index_value,
            columns=x,
            source_region_code=region_list,
            parameter_code=parameter_code,
            process_code=process_code,
            column_config=column_config,
            key_suffix="_ddc",
        )
    with c1:
        # create plot:
        st.markdown("**Figure:**")
        fig = px.box(df)
        st.plotly_chart(fig, use_container_width=True)
