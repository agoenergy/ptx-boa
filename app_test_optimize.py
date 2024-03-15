# -*- coding: utf-8 -*-
"""Test dashboard for optimization function."""
import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.graph_objects import Figure

from flh_opt.api_opt import optimize

st.set_page_config(layout="wide")

# Set the pandas display option to format floats with 2 decimal places
pd.set_option("display.float_format", "{:.2f}".format)

# Default input data
default_input_data = {
    "SOURCE_REGION_CODE": "ARG",
    "RES": [
        {
            "CAPEX_A": 30,
            "OPEX_F": 1,
            "OPEX_O": 0.01,
            "PROCESS_CODE": "PV-FIX",
        },
        {
            "CAPEX_A": 100,
            "OPEX_F": 1,
            "OPEX_O": 0.02,
            "PROCESS_CODE": "WIND-ON",
        },
    ],
    "ELY": {"EFF": 0.75, "CAPEX_A": 50, "OPEX_F": 5, "OPEX_O": 0.1},
    "EL_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
    "H2_STR": {"EFF": 1, "CAPEX_A": 10, "OPEX_F": 1, "OPEX_O": 0.1},
    "SPECCOST": {"H2O": 0.658},
}

# Create a form
with st.sidebar:
    with st.form(key="my_form"):
        st.write('Edit the values and press "Submit" to update the data.')

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
                                item_data[k] = st.text_input(
                                    f"{key} {i+1} {k}", value=v
                                )
                            else:
                                item_data[k] = st.number_input(
                                    f"{key} {i+1} {k}", value=v
                                )
                        input_data[key].append(item_data)
                elif isinstance(value, dict):
                    input_data[key] = {}
                    for k, v in value.items():
                        if isinstance(v, str):
                            input_data[key][k] = st.text_input(f"{key} {k}", value=v)
                        else:
                            input_data[key][k] = st.number_input(f"{key} {k}", value=v)
                else:
                    input_data[key] = st.text_input(key, value=value)

        # Create a submit button
        submit_button = st.form_submit_button(label="Submit")


# call optimization:
def call_optimize(input_data: dict):
    return optimize(input_data)


# add vertical lines:
def add_vertical_lines(fig: Figure, x_values: list):
    for i in range(0, len(x_values), 7 * 24):
        fig.add_vline(i, line_width=0.5)


# Call the optimize function when the submit button is clicked
if submit_button:
    result, n = call_optimize(input_data)
    res = n.statistics()

    st.subheader("Capacity, full load hours and costs")
    res2 = pd.DataFrame()
    res2["Capacity (MW per MW H2 output)"] = res["Optimal Capacity"]
    res2["flh (h/a)"] = res["Capacity Factor"] * 8760
    res2["total cost (USD/MWhH2)"] = (
        (res["Capital Expenditure"] + res["Operational Expenditure"]) / 8760 * 1000
    )
    res2.loc["Total", "total cost (USD/MWhH2)"] = res2["total cost (USD/MWhH2)"].sum()
    st.dataframe(res2.round(1))
    st.subheader("Aggregate results")
    st.dataframe(res.round(2))

    supply = n.statistics.supply(aggregate_time=False).reset_index()

    supply2 = supply.melt(id_vars=["component", "carrier"])

    st.subheader("Bus profiles")
    eb = (
        n.statistics.energy_balance(aggregate_time=False)
        .reset_index()
        .melt(id_vars=["component", "carrier", "bus_carrier"])
    )
    eb["component2"] = eb["component"] + " (" + eb["carrier"] + ")"

    fig = px.bar(
        eb,
        x="snapshot",
        y="value",
        facet_row="bus_carrier",
        color="component2",
        height=800,
        labels={"value": "MW"},
    )
    fig.update_layout(bargap=0)
    add_vertical_lines(fig, n.snapshots)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Storage State of Charge")
    soc = n.storage_units_t["state_of_charge"]
    fig = px.line(soc, labels={"value": "MW"})
    add_vertical_lines(fig, n.snapshots)
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
    add_vertical_lines(fig, n.snapshots)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("Data"):
        st.dataframe(supply2)
