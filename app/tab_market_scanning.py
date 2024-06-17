# -*- coding: utf-8 -*-
"""Content of market scanning tab."""
import pandas as pd
import plotly.express as px
import streamlit as st

from app.excel_download import prepare_and_download_df_as_excel
from app.ptxboa_functions import (
    calculate_results_list,
    change_index_names,
    config_number_columns,
    get_region_list_without_subregions,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI


def content_market_scanning(api: PtxboaAPI, cd: dict) -> None:
    """Create content for the "market scanning" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.
    cd: dict
        context data.
    """
    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_market_scanning.md"))

    res_costs = calculate_results_list(
        api,
        parameter_to_change="region",
        parameter_list=get_region_list_without_subregions(
            api,
            country_name=st.session_state["country"],
            keep=st.session_state["subregion"],
        ),
    )

    # get input data:
    input_data = api.get_input_data(st.session_state["scenario"])

    # filter shipping and pipeline distances:
    distances = input_data.loc[
        (input_data["parameter_code"].isin(["shipping distance", "pipeline distance"]))
        & (input_data["target_country_code"] == st.session_state["country"]),
        ["source_region_code", "parameter_code", "value"],
    ]
    distances = distances.pivot_table(
        index="source_region_code",
        columns="parameter_code",
        values="value",
        aggfunc="sum",
    )

    # merge costs and distances:
    df = pd.DataFrame()
    df["total costs"] = res_costs["Total"]
    df = df.merge(distances, left_index=True, right_index=True)

    # merge RE supply potential from context data:
    df = df.merge(
        cd["supply"].set_index("country_name")[
            ["re_tech_pot_EWI", "re_tech_pot_PTXAtlas"]
        ],
        left_index=True,
        right_index=True,
        how="left",
    )

    # prettify column names:
    df.rename(
        {
            "total costs": f"Total costs ({st.session_state['output_unit']})",
            "shipping distance": "Shipping distance (km)",
            "pipeline distance": "Pipeline distance (km)",
            "re_tech_pot_EWI": "RE technical potential (EWI) (TWh/a)",
            "re_tech_pot_PTXAtlas": "RE technical potential (PTX Atlas) (TWh/a)",
        },
        inplace=True,
        axis=1,
    )

    # replace nan entries:
    df = df.replace({"no potential": None, "no analysis ": None})
    df = df.astype(float)

    # if a subregion is selected, distribute country potential equally across
    # subregions:
    if st.session_state["subregion"] is not None:
        region = st.session_state["region"].split(" (")[0]
        number_of_subregions = (
            api.get_dimension("region")["region_name"].str.startswith(region).sum() - 1
        )
        for par in [
            "RE technical potential (PTX Atlas) (TWh/a)",
            "RE technical potential (EWI) (TWh/a)",
        ]:
            df.at[st.session_state["subregion"], par] = (
                df.at[region, par] / number_of_subregions
            )

    with st.container(border=True):
        st.markdown(
            "### Costs and transportation distances from different supply regions"
            f" to {st.session_state['country']}"
        )

        c1, c2 = st.columns(2)
        with c1:
            # select which distance to show:
            selected_distance = st.radio(
                "Select parameter to show on horizontal axis:",
                ["Shipping distance (km)", "Pipeline distance (km)"],
                key="selected_distance_supply_regions",
            )

        with c2:
            # select parameter for marker size:
            parameter_for_marker_size = st.radio(
                "Select parameter to scale marker size:",
                [
                    "RE technical potential (EWI) (TWh/a)",
                    "RE technical potential (PTX Atlas) (TWh/a)",
                    "None",
                ],
                help=read_markdown_file("md/helptext_technical_potential.md"),
            )

        # create plot:
        df_plot = df.copy().round(0)

        # distinguish between selected region and others:
        df_plot["category"] = "other regions"
        df_plot.at[st.session_state["region"], "category"] = "selected supply region"

        if parameter_for_marker_size == "None":
            fig = px.scatter(
                df_plot,
                x=selected_distance,
                y=f"Total costs ({st.session_state['output_unit']})",
                color="category",
                color_discrete_sequence=["#1A667B", "#D05094"],
                text=df_plot.index,
            )
            fig.update_traces(textposition="top center")
        else:
            df_plot = df_plot.loc[df_plot[parameter_for_marker_size] > 0]
            fig = px.scatter(
                df_plot,
                x=selected_distance,
                y=f"Total costs ({st.session_state['output_unit']})",
                size=parameter_for_marker_size,
                size_max=50,
                color="category",
                color_discrete_sequence=["#1A667B", "#D05094"],
                text=df_plot.index,
            )
            fig.update_traces(textposition="top center")

        st.plotly_chart(fig, use_container_width=True)

        # show data in tabular form:
        with st.expander("**Data**"):
            column_config = config_number_columns(df, format="%.0f")
            st.dataframe(
                df,
                use_container_width=True,
                column_config=column_config,
            )

            fn = "market_scanning_supply_regions"
            prepare_and_download_df_as_excel(df, filename=fn)

    with st.container(border=True):
        st.markdown(
            f"### Transportation distances from {st.session_state['region']}"
            " to different target countries"
        )

        # filter shipping and pipeline distances:
        df = input_data.loc[
            (
                input_data["parameter_code"].isin(
                    ["shipping distance", "pipeline distance"]
                )
            )
            & (input_data["source_region_code"] == st.session_state["region"]),
            ["target_country_code", "parameter_code", "value"],
        ]
        df = df.pivot_table(
            index="target_country_code",
            columns="parameter_code",
            values="value",
            aggfunc="sum",
        )

        # merge H2 demand from context data:

        # H2 demand data hard coded from excel tool.
        # TODO: improve data representation in context_data.xlsx
        # and take data from there.
        df["h2_demand_2030"] = None

        df.at["China", "h2_demand_2030"] = 35
        df.at["France", "h2_demand_2030"] = None
        df.at["Germany", "h2_demand_2030"] = 3
        df.at["India", "h2_demand_2030"] = 10
        df.at["Japan", "h2_demand_2030"] = 3
        df.at["Netherlands", "h2_demand_2030"] = None
        df.at["South Korea", "h2_demand_2030"] = 2
        df.at["Spain", "h2_demand_2030"] = None
        df.at["USA", "h2_demand_2030"] = 10

        # EU data is missing completely in context_data.xlsx:
        df.at["EU", "shipping distance"] = df.at["France", "shipping distance"]
        try:
            df.at["EU", "pipeline distance"] = df.at["France", "pipeline distance"]
        except KeyError:
            df.at["EU", "pipeline distance"] = None
        df.at["EU", "h2_demand_2030"] = 20

        df["h2_demand_2030"] = df["h2_demand_2030"].astype(float)

        # prettify column names:
        df.rename(
            {
                "shipping distance": "Shipping distance (km)",
                "pipeline distance": "Pipeline distance (km)",
                "h2_demand_2030": "Projected H2 demand in 2030 (Mt/a)",
            },
            inplace=True,
            axis=1,
        )

        # select parameter to display on x axis:
        selected_distance = st.radio(
            "Select parameter to show on horizontal axis:",
            ["Shipping distance (km)", "Pipeline distance (km)"],
            key="selected_distance_target_countries",
        )

        # create plot:
        df = change_index_names(df, mapping={"target_country_code": "Target country"})
        df_plot = df.copy().round(0)

        # distinguish between selected region and others:
        df_plot["category"] = "other countries"
        df_plot.at[st.session_state["country"], "category"] = "selected target country"

        fig = px.scatter(
            df_plot,
            x=selected_distance,
            y="Projected H2 demand in 2030 (Mt/a)",
            color="category",
            color_discrete_sequence=["#1A667B", "#D05094"],
            text=df_plot.index,
        )
        fig.update_traces(textposition="top center")

        st.plotly_chart(fig, use_container_width=True)

        with st.expander("**Data**"):
            st.dataframe(df, use_container_width=True)
            fn = "market_scanning_target_countries"
            prepare_and_download_df_as_excel(df, filename=fn)
