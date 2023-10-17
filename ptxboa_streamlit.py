# -*- coding: utf-8 -*-
"""Mockup streamlit app."""
import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

import app.ptxboa_functions as pf
from ptxboa.api import PtxboaAPI

# app layout:

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)

st.set_page_config(layout="wide")
st.title("PtX Business Opportunity Analyzer Mockup")
(
    t_dashboard,
    t_market_scanning,
    t_costs_by_region,
    t_country_fact_sheets,
    t_certification_schemes,
    t_sustainability,
    t_literature,
    t_disclaimer,
) = st.tabs(
    [
        "Dashboard",
        "Market scanning",
        "Costs by region",
        "Country fact sheets",
        "Certification schemes",
        "Sustainability",
        "Literature",
        "Disclaimer",
    ]
)

# TODO: cache this instance
api = PtxboaAPI()

# create sidebar:
settings = pf.create_sidebar(api)


# calculate results:


res_details = pf.calculate_results(api, settings)


def aggregate_costs(res_details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detailed costs."""
    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index="region", columns="process_type", values="values", aggfunc=sum
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    # TODO exclude countries with total costs of 0 - maybe remove later:
    res = res.loc[res["Total"] != 0]
    return res


res_costs = aggregate_costs(res_details)


# import context data:
cd = pf.import_context_data()


# dashboard:
with t_dashboard:
    pf.content_dashboard(api, res_costs, cd, settings)

with t_market_scanning:
    st.markdown("**Market Scanning**")
    st.markdown(
        """This is the markt scanning sheet. It will contain scatter plots
        that allows users to compare regions by total cost, transportation
        distance and H2 demand."""
    )
    [c1, c2] = st.columns(2)
    with c1:
        fig = px.scatter(
            res_costs,
            x="Transportation (Pipeline)",
            y="Total",
            title="Costs and transportation distances",
            height=600,
        )
        # Add text above markers
        fig.update_traces(
            text=api.get_dimension("region")["region_code"],
            textposition="top center",
            mode="markers+text",
        )

        st.plotly_chart(fig)


with t_costs_by_region:
    st.markdown("**Costs by region**")
    st.markdown(
        """On this sheet, users can analyze total cost and cost components for
          different supply countries. Data is represented as a bar chart and
            in tabular form. \n\n Data can be filterend and sorted."""
    )
    # filter data:
    df_res = res_costs.copy()
    show_which_data = st.radio(
        "Select regions to display:", ["All", "Ten cheapest", "Manual select"], index=0
    )
    if show_which_data == "Ten cheapest":
        df_res = df_res.nsmallest(10, "Total")
    elif show_which_data == "Manual select":
        ind_select = st.multiselect(
            "Select regions:", df_res.index.values, default=df_res.index.values
        )
        df_res = df_res.loc[ind_select]

    sort_ascending = st.toggle("Sort by total costs?", value=True)
    if sort_ascending:
        df_res = df_res.sort_values(["Total"], ascending=True)
    pf.create_bar_chart_costs(df_res)

    st.subheader("Costs as data frame:")
    st.dataframe(res_costs, use_container_width=True)

with t_country_fact_sheets:
    pf.create_fact_sheet_demand_country(cd, settings["sel_country_name"])
    st.divider()
    pf.create_fact_sheet_supply_country(cd, settings["sel_region"])

with t_certification_schemes:
    pf.create_fact_sheet_certification_schemes(cd)

with t_sustainability:
    pf.create_content_sustainability(cd)

with t_literature:
    pf.create_content_literature(cd)

with t_disclaimer:
    st.markdown("**Disclaimer**")
    st.markdown(
        """This is the disclaimer.
        Images can be imported directly as image files."""
    )
    st.image(Image.open("static/disclaimer.png"))
    st.image(Image.open("static/disclaimer_2.png"))
