# -*- coding: utf-8 -*-
"""Content of optimization tab."""
import pandas as pd
import plotly.graph_objects as go
import pypsa
import streamlit as st

from app.network_download import download_network_as_netcdf
from app.ptxboa_functions import read_markdown_file
from ptxboa.api import PtxboaAPI


def content_optimization(api: PtxboaAPI) -> None:
    st.subheader("Optimization results")
    st.warning("Warning: Preliminary debugging results. ")

    with st.expander("What is this?"):
        st.markdown(read_markdown_file("md/whatisthis_optimization.md"))

    try:
        n, metadata = api.get_flh_opt_network(
            scenario=st.session_state["scenario"],
            secproc_co2=st.session_state["secproc_co2"],
            secproc_water=st.session_state["secproc_water"],
            chain=st.session_state["chain"],
            res_gen=st.session_state["res_gen"],
            region=st.session_state["region"],
            country=st.session_state["country"],
            transport=st.session_state["transport"],
            ship_own_fuel=st.session_state["ship_own_fuel"],
            user_data=st.session_state["user_changes_df"],
        )
    except FileNotFoundError:
        st.error("No optimization model could be loaded")
        return

    if metadata["model_status"] == ["ok", "optimal"]:

        res = calc_aggregate_statistics(n)
        with st.expander("Aggregate statistics"):
            st.dataframe(res.round(2), use_container_width=True)

        with st.expander("Profiles"):
            create_profile_figure(n)

        with st.expander("Input data"):
            show_input_data(n)

    else:
        st.error(
            f"No optimal solution! -> model status is {st.session_state['model_status']}"  # noqa
        )

    download_network_as_netcdf(st.session_state["network"], "network.nc")


# calculate aggregate statistics:
def calc_aggregate_statistics(n: pypsa.Network) -> pd.DataFrame:
    res = pd.DataFrame()
    for g in [
        "PV-FIX",
        "WIND-ON",
        "WIND-OFF",
    ]:
        if g in n.generators.index:
            res.at[g, "Capacity (kW)"] = n.generators.at[g, "p_nom_opt"]
            res.at[g, "Output (kWh/a)"] = (
                n.generators_t["p"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "CAPEX (USD/kW)"] = n.generators.at[g, "capital_cost"]
            res.at[g, "OPEX (USD/kWh)"] = n.generators.at[g, "marginal_cost"]

    for g in ["ELY", "DERIV", "H2_STR_in"]:
        if g in n.links.index:
            res.at[g, "Capacity (kW)"] = (
                n.links.at[g, "p_nom_opt"] * n.links.at[g, "efficiency"]
            )
            res.at[g, "Output (kWh/a)"] = (
                -n.links_t["p1"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "CAPEX (USD/kW)"] = (
                n.links.at[g, "capital_cost"] / n.links.at[g, "efficiency"]
            )
            res.at[g, "OPEX (USD/kWh)"] = n.links.at[g, "marginal_cost"]

    for g in ["EL_STR"]:
        if g in n.storage_units.index:
            res.at[g, "Capacity (kW)"] = n.storage_units.at[g, "p_nom_opt"]
            res.at[g, "Output (kWh/a)"] = (
                n.storage_units_t["p_dispatch"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "CAPEX (USD/kW)"] = n.storage_units.at[g, "capital_cost"]
            res.at[g, "OPEX (USD/kWh)"] = n.storage_units.at[g, "marginal_cost"]

    for g in [
        "CO2-G_supply",
        "H2O-L_supply",
        "HEAT_supply",
        "N2-G_supply",
    ]:
        if g in n.generators.index:
            res.at[g, "Output (kWh/a)"] = (
                n.generators_t["p"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "OPEX (USD/kWh)"] = n.generators.at[g, "marginal_cost"]

    res = res.fillna(0)

    res["Full load hours (h)"] = res["Output (kWh/a)"] / res["Capacity (kW)"]
    res["Cost (USD/MWh)"] = (
        (
            res["Capacity (kW)"] * res["CAPEX (USD/kW)"]
            + res["Output (kWh/a)"] * res["OPEX (USD/kWh)"]
        )
        / 8760
        * 1000
    )

    res.at["Total", "Cost (USD/MWh)"] = res["Cost (USD/MWh)"].sum()

    # rename components:
    rename_list = {
        "PV-FIX": "PV tilted",
        "WIND-ON": "Wind onshore",
        "WIND-OFF": "Wind offshore",
        "ELY": "Electrolyzer",
        "DERIV": "Derivate production",
        "H2_STR_in": "H2 storage",
        "EL_STR": "Electricity storage",
        "CO2-G_supply": "CO2 supply",
        "H2O-L_supply": "Water supply",
    }
    res = res.rename(rename_list, axis=0)
    return res


def create_profile_figure(n: pypsa.Network) -> None:
    def transform_time_series(
        df: pd.DataFrame, parameter: str = "Power"
    ) -> pd.DataFrame:
        res = df.reset_index().melt(
            id_vars=["timestep", "period"],
            var_name="Component",
            value_name="MW (MWh for SOC)",
        )
        res["Parameter"] = parameter
        return res

    df_p_max_pu = n.generators_t["p_max_pu"]
    df_p_max_pu = transform_time_series(df_p_max_pu, parameter="cap. factor")
    df_gen = n.generators_t["p"]
    df_gen = transform_time_series(df_gen)
    df_links = -n.links_t["p1"]
    df_links = transform_time_series(df_links)
    df_store = n.stores_t["e"]
    df_store = transform_time_series(df_store)
    df_storageunit = n.storage_units_t["state_of_charge"]
    df_storageunit = transform_time_series(df_storageunit)

    df = pd.concat([df_p_max_pu, df_gen, df_links, df_store, df_storageunit])

    # selection:
    df = df.loc[
        df["Component"].isin(
            [
                "PV-FIX",
                "WIND-ON",
                "WIND-OFF",
                "ELY",
                "DERIV",
                "H2_STR_store",
                "EL_STR",
                "final_product_storage",
            ]
        )
    ]

    # rename components:
    rename_list = {
        "PV-FIX": "PV tilted",
        "WIND-ON": "Wind onshore",
        "WIND-OFF": "Wind offshore",
        "ELY": "Electrolyzer",
        "DERIV": "Derivate production",
        "H2_STR_in": "H2 storage",
        "H2_STR_store": "H2 storage",
        "final_product_storage": "Final product storage",
        "EL_STR": "Electricity storage",
        "CO2-G_supply": "CO2 supply",
        "H2O-L_supply": "Water supply",
    }
    df = df.replace(rename_list)

    df_sel = df

    # add continous time index:
    df_sel["period"] = df_sel["period"].astype(int)
    df_sel["timestep"] = df_sel["timestep"].astype(int)
    df_sel["time"] = 7 * 24 * df_sel["period"] + df_sel["timestep"]
    df_sel = df_sel.sort_values("time")

    # generation:
    st.subheader("Output")
    fig = go.Figure()

    def add_vertical_lines(fig: go.Figure):
        """Add vertical lines between periods."""
        for x in range(7 * 24, 7 * 8 * 24, 7 * 24):
            fig.add_vline(x=x, line_color="black", line_width=0.5)

    def add_to_figure(
        df: pd.DataFrame,
        fig: go.Figure,
        component: str,
        parameter: str,
        color: str,
        fill: bool = False,
    ):
        df_plot = df[(df["Component"] == component)]
        df_plot = df_plot[(df_plot["Parameter"] == parameter)]
        if fill:
            fig.add_trace(
                go.Line(
                    x=df_plot["time"],
                    y=df_plot["MW (MWh for SOC)"],
                    name=component,
                    line_color=color,
                    stackgroup="one",
                )
            )
        else:
            fig.add_trace(
                go.Line(
                    x=df_plot["time"],
                    y=df_plot["MW (MWh for SOC)"],
                    name=component,
                    line_color=color,
                )
            )

    add_to_figure(
        df_sel, fig, component="PV tilted", parameter="Power", fill=True, color="yellow"
    )
    add_to_figure(
        df_sel,
        fig,
        component="Wind onshore",
        parameter="Power",
        fill=True,
        color="blue",
    )
    add_to_figure(
        df_sel,
        fig,
        component="Wind offshore",
        parameter="Power",
        fill=True,
        color="blue",
    )
    add_to_figure(
        df_sel, fig, component="Electrolyzer", parameter="Power", color="black"
    )
    add_to_figure(
        df_sel, fig, component="Derivate production", parameter="Power", color="red"
    )

    add_vertical_lines(fig)

    fig.update_layout(
        xaxis={"title": "time (h)"},
        yaxis={"title": "output (MW)"},
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Storage state of charge")
    include_final_product_storage = st.toggle("Show final product storage", value=False)
    # storage figure:
    fig = go.Figure()

    add_to_figure(
        df_sel,
        fig,
        component="Electricity storage",
        parameter="Power",
        color="black",
    )

    add_to_figure(
        df_sel,
        fig,
        component="H2 storage",
        parameter="Power",
        color="red",
    )
    if include_final_product_storage:
        add_to_figure(
            df_sel,
            fig,
            component="Final product storage",
            parameter="Power",
            color="blue",
        )

    add_vertical_lines(fig)

    fig.update_layout(
        xaxis={"title": "time (h)"},
        yaxis={"title": "state of charge (MWh)"},
    )

    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Capacity factors")

    fig = go.Figure()
    add_to_figure(
        df_sel, fig, component="PV tilted", parameter="cap. factor", color="yellow"
    )
    add_to_figure(
        df_sel,
        fig,
        component="Wind onshore",
        parameter="cap. factor",
        color="blue",
    )
    add_to_figure(
        df_sel,
        fig,
        component="Wind offshore",
        parameter="cap. factor",
        color="blue",
    )
    add_vertical_lines(fig)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Profile data")
    st.dataframe(df_sel, use_container_width=True)


def show_filtered_df(
    df: pd.DataFrame, drop_empty: bool, drop_zero: bool, drop_one: bool
):
    for c in df.columns:
        if (
            df[c].eq("PQ").all()
            or (drop_empty and df[c].isnull().all())
            or (drop_empty and df[c].eq("").all())
            or (drop_zero and df[c].eq(0).all())
            or (drop_one and df[c].eq(1).all())
        ):
            df.drop(columns=c, inplace=True)
    st.write(df)


def show_input_data(n: pypsa.Network) -> None:
    drop_empty = st.toggle("Drop empty columns", False)
    drop_zero = st.toggle("Drop  columns with only zeros", False)
    drop_one = st.toggle("Drop columns with only ones", False)
    show_filtered_df(n.carriers.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.buses.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.loads.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.generators.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.links.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.storage_units.copy(), drop_empty, drop_zero, drop_one)
    show_filtered_df(n.stores.copy(), drop_empty, drop_zero, drop_one)
