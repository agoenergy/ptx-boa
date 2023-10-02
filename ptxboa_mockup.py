# -*- coding: utf-8 -*-
"""Mockup streamlit app."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from faker import Faker
from PIL import Image

import ptxboa.functions as pf
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
    t_context_data,
    t_disclaimer,
) = st.tabs(
    ["Dashboard", "Market scanning", "Costs by region", "Context data", "Disclaimer"]
)

# TODO: cache this instance
api = PtxboaAPI()

# create sidebar:
settings = pf.create_sidebar(api)

# calculate results:


@st.cache_data()
def get_results(settings):
    res_costs = pd.DataFrame(
        index=api.get_dimensions()["region"].index,
        columns=["A", "B", "C", "D"],
        data=np.random.rand(len(api.get_dimensions()["region"].index), 4),
    )
    res_costs["Total"] = res_costs.sum(axis=1)
    return res_costs


res_costs = get_results(settings)


# dashboard:
with t_dashboard:
    pf.content_dashboard(res_costs, settings)

with t_market_scanning:
    st.markdown("**Market Scanning**")
    st.markdown(Faker().text())
    st.markdown(Faker().text())
    [c1, c2] = st.columns(2)
    with c1:
        fig = px.scatter(
            res_costs,
            x="A",
            y="B",
            text=res_costs.index,
            title="Costs and transportation distances",
        )
        st.plotly_chart(fig)
    with c2:
        fig = px.scatter(
            res_costs,
            x="A",
            y="B",
            text=res_costs.index,
            title="Transportation distances 2",
        )
        st.plotly_chart(fig)

with t_costs_by_region:
    st.markdown("**Costs by region**")
    st.markdown(Faker().text())
    st.markdown(Faker().text())
    df_res = res_costs.copy()
    sort_ascending = st.toggle("Sort by total costs?", value=True)
    if sort_ascending:
        df_res = df_res.sort_values(["Total"], ascending=True)
    pf.create_bar_chart_costs(df_res)

    st.subheader("Costs as data frame:")
    st.dataframe(res_costs, use_container_width=True)

with t_context_data:
    st.markdown("**Context data**")
    st.markdown(Faker().text())
    st.markdown(Faker().text())

with t_disclaimer:
    st.markdown("**Disclaimer**")
    st.markdown(Faker().text())
    st.markdown(Faker().text())
    st.image(Image.open("static/disclaimer.png"))
    st.image(Image.open("static/disclaimer_2.png"))
