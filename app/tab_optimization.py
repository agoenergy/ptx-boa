# -*- coding: utf-8 -*-
"""Content of optimization tab."""
import pandas as pd
import plotly.express as px
import streamlit as st
from plotly.graph_objects import Figure

from ptxboa.api import PtxboaAPI


def content_optimization(api: PtxboaAPI) -> None:
    st.subheader("Optimization results")
    st.warning("Warning: Preliminary debugging results. ")

    if st.session_state["model_status"] == "optimal":
        input_data = api.get_input_data(st.session_state["scenario"])
        n = st.session_state["network"]

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
            # * input_data["ELY"]["EFF"]
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
                # * input_data["DERIV"]["EFF"]
            )

        res2["flh (h/a)"] = res["Capacity Factor"] * 8760
        res2["total cost (USD/MWh final product)"] = (
            (res["Capital Expenditure"] + res["Operational Expenditure"]) / 8760 * 1000
        )
        res2.loc["Total", "total cost (USD/MWh final product)"] = res2[
            "total cost (USD/MWh final product)"
        ].sum()

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

        st.subheader("Capacity, full load hours and costs")

        st.dataframe(res2.round(1))
        st.subheader("Aggregate results")
        st.dataframe(res.round(2))

        # add vertical lines:
        def add_vertical_lines(fig: Figure, x_values: list):
            for i in range(0, len(x_values), 7 * 24):
                fig.add_vline(i, line_width=0.5)

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
    else:
        st.error(
            f"No optimal solution! -> model status is {st.session_state['model_status']}"  # noqa
        )
