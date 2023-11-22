# -*- coding: utf-8 -*-
"""Content of input data tab."""
import plotly.express as px
import streamlit as st

from app.plot_functions import plot_input_data_on_map
from app.ptxboa_functions import display_and_edit_data_table, display_user_changes
from ptxboa.api import PtxboaAPI


def content_input_data(api: PtxboaAPI) -> None:
    """Create content for the "input data" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Input data**

This tab gives you an overview of model input data that is country-specific.
This includes full load hours (FLH) and capital expenditures (CAPEX)
of renewable generation technologies, weighted average cost of capital (WACC),
as well as shipping and pipeline distances to the chosen demand country.
The box plots show median, 1st and 3rd quartile as well as the total spread of values.
They also show the data for your country for comparison.
            """
        )

    st.subheader("Region specific data")
    # get input data:
    input_data = api.get_input_data(
        st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    # filter data:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )
    input_data_without_subregions = input_data.loc[
        input_data["source_region_code"].isin(region_list_without_subregions)
    ]

    list_data_types = ["CAPEX", "full load hours", "interest rate"]
    data_selection = st.radio("Select data type", list_data_types, horizontal=True)
    if data_selection == "CAPEX":
        parameter_code = ["CAPEX"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        x = "process_code"
        missing_index_name = "parameter_code"
        missing_index_value = "CAPEX"
        column_config = {"format": "%.0f USD/kW", "min_value": 0}

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

    if data_selection == "interest rate":
        parameter_code = ["interest rate"]
        process_code = [""]
        x = "parameter_code"
        column_config = {"format": "%.3f", "min_value": 0, "max_value": 1}
        missing_index_name = "parameter_code"
        missing_index_value = "interest rate"

    c1, c2 = st.columns([2, 1], gap="large")
    with c1:
        st.markdown("**Map**")
        if data_selection in ["full load hours", "CAPEX"]:
            map_parameter = st.selectbox(
                "Show Parameter on Map", process_code, key="input_data_map_parameter"
            )
        else:
            map_parameter = "interest rate"
        fig = plot_input_data_on_map(
            api=api,
            data_type=data_selection,
            color_col=map_parameter,
            scope="world",
        )
        st.plotly_chart(fig, use_container_width=True)

    with st.expander("**Data**"):
        df = display_and_edit_data_table(
            input_data=input_data_without_subregions,
            missing_index_name=missing_index_name,
            missing_index_value=missing_index_value,
            columns=x,
            source_region_code=region_list_without_subregions,
            parameter_code=parameter_code,
            process_code=process_code,
            column_config=column_config,
        )
    with c2:
        # create plot:
        st.markdown("**Regional Distribution**")
        fig = px.box(df)
        st.plotly_chart(fig, use_container_width=True)

    st.divider()
    st.subheader("Data that is identical for all regions")

    input_data_global = input_data.loc[input_data["source_region_code"] == ""]

    # filter processes:
    processes = api.get_dimension("process")

    list_processes_transport = processes.loc[
        processes["is_transport"], "process_name"
    ].to_list()

    list_processes_not_transport = processes.loc[
        ~processes["is_transport"], "process_name"
    ].to_list()
    st.markdown("**Conversion processes:**")
    df = display_and_edit_data_table(
        input_data_global,
        missing_index_name="source_region_code",
        missing_index_value=None,
        parameter_code=[
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ],
        process_code=list_processes_not_transport,
        index="process_code",
        columns="parameter_code",
    )
    st.markdown("**Transportation processes:**")
    st.markdown("TODO: fix data")
    df = display_and_edit_data_table(
        input_data_global,
        missing_index_name="source_region_code",
        missing_index_value=None,
        parameter_code=[
            "losses (own fuel, transport)",
            "levelized costs",
            "lifetime / amortization period",
            # FIXME: add bunker fuel consumption
        ],
        process_code=list_processes_transport,
        index="process_code",
        columns="parameter_code",
    )

    # If there are user changes, display them:
    display_user_changes()
