# -*- coding: utf-8 -*-
"""Content of optimization tab."""
import pandas as pd
import plotly.express as px
import pypsa
import streamlit as st

from app.network_download import download_network_as_netcdf
from ptxboa.api import PtxboaAPI


def content_optimization(api: PtxboaAPI) -> None:
    st.subheader("Optimization results")
    st.warning("Warning: Preliminary debugging results. ")

    if st.session_state["model_status"] == "optimal":
        n = st.session_state["network"]

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
    def transform_time_series(df: pd.DataFrame, parameter: str = None) -> pd.DataFrame:
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
            ]
        )
    ]
    df["Type"] = "Power"

    ind1 = df["Component"].isin(
        (
            "PV-FIX",
            "WIND-ON",
            "WIND-OFF",
        )
    )
    ind2 = df["Parameter"] == "cap. factor"
    df.loc[ind1 & ind2, "Type"] = "cap. factor"

    ind = df["Component"].isin(["ELY"])
    df.loc[ind, "Type"] = "H2"

    ind = df["Component"].isin(["H2_STR_store", "EL_STR", "final_product_storage"])
    df.loc[ind, "Type"] = "SOC"

    ind = df["Component"].isin(["ELY"])
    df.loc[ind, "Type"] = "H2"

    ind = df["Component"].isin(["DERIV"])
    df.loc[ind, "Type"] = "Derivate"

    # rename components:
    rename_list = {
        "PV-FIX": "PV tilted",
        "WIND-ON": "Wind onshore",
        "WIND-OFF": "Wind offshore",
        "ELY": "Electrolyzer",
        "DERIV": "Derivate production",
        "H2_STR_in": "H2 storage",
        "H2_STR_store": "H2 storage",
        "EL_STR": "Electricity storage",
        "CO2-G_supply": "CO2 supply",
        "H2O-L_supply": "Water supply",
    }
    df = df.replace(rename_list)

    # filter:
    types_all = df["Type"].unique().tolist()
    types_sel = st.multiselect("Data types to display:", types_all, default=types_all)

    periods_all = df["period"].unique().tolist()
    periods_sel = st.multiselect(
        "Periods to display:", periods_all, default=periods_all
    )
    df_sel = df.loc[(df["Type"].isin(types_sel)) & (df["period"].isin(periods_sel))]

    # add continous time index:
    df_sel["period"] = df_sel["period"].astype(int)
    df_sel["timestep"] = df_sel["timestep"].astype(int)
    df_sel["time"] = 7 * 24 * df_sel["period"] + df_sel["timestep"]
    df_sel = df_sel.sort_values("time")

    fig = px.line(
        df_sel,
        x="time",
        y="MW (MWh for SOC)",
        color="Component",
        facet_row="Type",
        height=800,
    )
    fig.update_yaxes(matches=None, showticklabels=True)

    # add vertical lines between periods:
    for x in range(7 * 24, 7 * 8 * 24, 7 * 24):
        fig.add_vline(x=x, line_color="black")
    st.plotly_chart(fig, use_container_width=True)

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
