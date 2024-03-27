# -*- coding: utf-8 -*-
"""Test dashboard for optimization function."""
from json import load
from time import time
from typing import Dict, List

import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.graph_objects import Figure

from flh_opt.api_opt import optimize

st.set_page_config(layout="wide")

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)


# load input data from json:
def load_json(filename: str) -> List[Dict]:
    """Load input data from json file."""
    with open(filename, "r") as f:
        api_test_settings = load(f)

    # extract ids:
    api_test_settings_names = []
    for i in api_test_settings:
        api_test_settings_names.append(i["id"])
    return [api_test_settings, api_test_settings_names]


[api_test_settings, api_test_settings_names] = load_json(
    "tests/test_optimize_settings.json"
)
test_case = st.selectbox("Select test case", api_test_settings_names)
default_input_data = api_test_settings[api_test_settings_names.index(test_case)]

with st.expander("Default input data"):
    st.write(default_input_data)

# Create a form
with st.sidebar:

    # Create widgets for each item in the data
    input_data = {}
    for key, value in default_input_data.items():
        with st.expander(key):
            if isinstance(value, list):
                input_data[key] = []
                for i, item in enumerate(value):
                    item_data = {}
                    for k, v in item.items():
                        if isinstance(v, str):
                            item_data[k] = st.text_input(f"{key} {i+1} {k}", value=v)
                        else:
                            item_data[k] = st.number_input(f"{key} {i+1} {k}", value=v)
                    input_data[key].append(item_data)
            elif isinstance(value, dict):
                input_data[key] = {}
                for k, v in value.items():
                    if isinstance(v, str):
                        input_data[key][k] = st.text_input(f"{key} {k}", value=v)
                    if isinstance(v, float) or isinstance(v, int):
                        input_data[key][k] = st.number_input(f"{key} {k}", value=v)
                    if isinstance(v, dict):
                        input_data[key][k] = v
            else:
                input_data[key] = st.text_input(key, value=value)


# add vertical lines:
def add_vertical_lines(fig: Figure, x_values: list):
    for i in range(0, len(x_values), 7 * 24):
        fig.add_vline(i, line_width=0.5)


@st.cache_data
def solve_model(input_data: Dict):
    start_time = time()
    result, n = optimize(input_data)
    end_time = time()
    run_time = end_time - start_time

    res = n.statistics()

    res2 = pd.DataFrame()

    # for links: calculate capacity in terms of output:
    res2["Capacity (MW per MW final product)"] = res["Optimal Capacity"]
    res2.loc[
        res2.index.isin([("Link", "H2")]), "Capacity (MW per MW final product)"
    ] = (
        res2.loc[
            res2.index.isin([("Link", "H2")]), "Capacity (MW per MW final product)"
        ]
        * input_data["ELY"]["EFF"]
    )
    if "DERIV" in input_data.keys():
        res2.loc[
            res2.index.isin([("Link", "final_product")]),
            "Capacity (MW per MW final product)",
        ] = (
            res2.loc[
                res2.index.isin([("Link", "final_product")]),
                "Capacity (MW per MW final product)",
            ]
            * input_data["DERIV"]["EFF"]
        )

    res2["flh (h/a)"] = res["Capacity Factor"] * 8760
    res2["total cost (USD/MWh final product)"] = (
        (res["Capital Expenditure"] + res["Operational Expenditure"]) / 8760 * 1000
    )
    res2.loc["Total", "total cost (USD/MWh final product)"] = res2[
        "total cost (USD/MWh final product)"
    ].sum()

    n.export_to_netcdf(f"tests/{input_data['id']}_via_streamlit.nc")

    supply = n.statistics.supply(aggregate_time=False).reset_index()

    supply2 = supply.melt(id_vars=["component", "carrier"])

    eb = (
        n.statistics.energy_balance(aggregate_time=False)
        .reset_index()
        .melt(id_vars=["component", "carrier", "bus_carrier"])
    )
    eb["component2"] = eb["component"] + " (" + eb["carrier"] + ")"

    soc = n.storage_units_t["state_of_charge"]

    snapshots = n.snapshots
    return [res, res2, supply2, eb, soc, snapshots, run_time]


# Call the optimize function when the submit button is clicked
[res, res2, supply2, eb, soc, snapshots, run_time] = solve_model(input_data)

st.info(f"Time to solve optimization problem: {run_time:.2f} seconds")

st.subheader("Capacity, full load hours and costs")

st.dataframe(res2.round(1))
st.subheader("Aggregate results")
st.dataframe(res.round(2))

st.subheader("Bus profiles")
all_bus_carriers = eb["bus_carrier"].unique()
select_bus_carriers = st.multiselect(
    "buses to show", all_bus_carriers, default=all_bus_carriers
)
eb_select = eb.loc[eb["bus_carrier"].isin(select_bus_carriers)]
fig = px.bar(
    eb_select,
    x="snapshot",
    y="value",
    facet_row="bus_carrier",
    color="component2",
    height=800,
    labels={"value": "MW"},
)
fig.update_layout(bargap=0)
add_vertical_lines(fig, snapshots)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Storage State of Charge")
fig = px.line(soc, labels={"value": "MW"})
add_vertical_lines(fig, snapshots)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Supply profiles")
fig = px.area(
    supply2,
    x="snapshot",
    y="value",
    facet_row="component",
    height=800,
    color="carrier",
    labels={"value": "MW"},
)
add_vertical_lines(fig, snapshots)
st.plotly_chart(fig, use_container_width=True)
with st.expander("Data"):
    st.dataframe(supply2)
