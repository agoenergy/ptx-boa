# -*- coding: utf-8 -*-
"""Content of optimization tab."""
import numpy as np
import pandas as pd
import pypsa
import streamlit as st

from app.network_download import download_network_as_netcdf
from app.plot_functions import (
    create_profile_figure_capacity_factors,
    create_profile_figure_generation,
    create_profile_figure_soc,
    prepare_data_for_profile_figures,
)
from app.ptxboa_functions import read_markdown_file
from ptxboa.api import PtxboaAPI


def content_optimization(api: PtxboaAPI) -> None:

    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_optimization.md"))

    with st.spinner("Please wait. Running optimization model..."):
        # load netcdf file:
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
        res_debug = calc_aggregate_statistics(n, include_debugging_output=True)
        df_sel = prepare_data_for_profile_figures(n)

        with st.container(border=True):
            st.subheader("Generation profiles")
            st.markdown(read_markdown_file("md/info_generation_profile_figure.md"))
            fig = create_profile_figure_generation(df_sel)
            st.plotly_chart(fig, use_container_width=True)

        with st.container(border=True):
            st.subheader("Capacities, full load hours and costs")
            st.markdown(read_markdown_file("md/info_optimization_results.md"))
            st.dataframe(
                res,
                use_container_width=True,
                column_config={
                    "Capacity (MW)": st.column_config.NumberColumn(format="%.1f"),
                    "Output (MWh/a)": st.column_config.NumberColumn(format="%.0f"),
                    "Full load hours (h)": st.column_config.NumberColumn(format="%.0f"),
                    "Curtailment (%)": st.column_config.NumberColumn(format="%.1f %%"),
                    "Cost (USD/MWh)": st.column_config.NumberColumn(format="%.1f"),
                },
            )

        with st.container(border=True):
            st.subheader("Download model")
            st.markdown(read_markdown_file("md/info_download_model.md"))
            download_network_as_netcdf(n=n, filename="network.nc")

        with st.expander("Debugging output"):
            st.warning(
                "This output is for debugging only. It will be hidden from end users by default."  # noqa
            )
            st.markdown("#### Aggregate statistics:")
            st.dataframe(res_debug)

            st.markdown("#### Storage state of charge")
            fig = create_profile_figure_soc(df_sel)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Capacity factors")
            fig = create_profile_figure_capacity_factors(df_sel)
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("#### Profile data")
            st.dataframe(df_sel, use_container_width=True)

            st.markdown("#### Input data")
            show_input_data(n)

    else:
        st.error(
            f"No optimal solution! -> model status is {st.session_state['model_status']}"  # noqa
        )


# calculate aggregate statistics:
def calc_aggregate_statistics(
    n: pypsa.Network, include_debugging_output: bool = False
) -> pd.DataFrame:
    res = pd.DataFrame()
    for g in [
        "PV-FIX",
        "WIND-ON",
        "WIND-OFF",
    ]:
        if g in n.generators.index:
            res.at[g, "Capacity (MW)"] = n.generators.at[g, "p_nom_opt"]
            res.at[g, "Output (MWh/a)"] = (
                n.generators_t["p"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "CAPEX (USD/kW)"] = n.generators.at[g, "capital_cost"]
            res.at[g, "OPEX (USD/kWh)"] = n.generators.at[g, "marginal_cost"]
            res.at[g, "Full load hours before curtailment (h)"] = (
                n.generators_t["p_max_pu"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "Curtailment (MWh/a)"] = (
                res.at[g, "Capacity (MW)"]
                * res.at[g, "Full load hours before curtailment (h)"]
                - res.at[g, "Output (MWh/a)"]
            )
            res.at[g, "Curtailment (%)"] = (
                100
                * res.at[g, "Curtailment (MWh/a)"]
                / (res.at[g, "Output (MWh/a)"] + res.at[g, "Curtailment (MWh/a)"])
            )

    for g in ["ELY", "DERIV", "H2_STR_in"]:
        if g in n.links.index:
            res.at[g, "Capacity (MW)"] = (
                n.links.at[g, "p_nom_opt"] * n.links.at[g, "efficiency"]
            )
            res.at[g, "Output (MWh/a)"] = (
                -n.links_t["p1"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "CAPEX (USD/kW)"] = (
                n.links.at[g, "capital_cost"] / n.links.at[g, "efficiency"]
            )
            res.at[g, "OPEX (USD/kWh)"] = n.links.at[g, "marginal_cost"]

    for g in ["EL_STR"]:
        if g in n.storage_units.index:
            res.at[g, "Capacity (MW)"] = n.storage_units.at[g, "p_nom_opt"]
            res.at[g, "Output (MWh/a)"] = (
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
            res.at[g, "Output (MWh/a)"] = (
                n.generators_t["p"][g] * n.snapshot_weightings["generators"]
            ).sum()
            res.at[g, "OPEX (USD/kWh)"] = n.generators.at[g, "marginal_cost"]

    res = res.fillna(0)

    res["Full load hours (h)"] = res["Output (MWh/a)"] / res["Capacity (MW)"]
    res["Cost (USD/MWh)"] = (
        (
            res["Capacity (MW)"] * res["CAPEX (USD/kW)"]
            + res["Output (MWh/a)"] * res["OPEX (USD/kWh)"]
        )
        / 8760
        * 1000
    )

    # rename components:
    rename_list = {
        "PV-FIX": "PV tilted",
        "WIND-ON": "Wind onshore",
        "WIND-OFF": "Wind offshore",
        "ELY": "Electrolyzer",
        "DERIV": "Derivative production",
        "H2_STR_in": "H2 storage",
        "EL_STR": "Electricity storage",
        "CO2-G_supply": "CO2 supply",
        "H2O-L_supply": "Water supply",
    }
    res = res.rename(rename_list, axis=0)

    # drop unwanted columns:
    if not include_debugging_output:

        # filter columns:
        res = res[
            [
                "Capacity (MW)",
                "Output (MWh/a)",
                "Full load hours (h)",
                "Curtailment (%)",
                "Cost (USD/MWh)",
            ]
        ]

        # filter rows:
        res = res[
            res.index.isin(
                [
                    "PV tilted",
                    "Wind onshore",
                    "Wind offshore",
                    "Electrolyzer",
                    "Derivative production",
                    "Electricity storage",
                    "H2 storage",
                ]
            )
        ]

        # remove unwanted entries:
        for i in ["Electricity storage", "H2 storage"]:
            for c in [
                "Output (MWh/a)",
                "Full load hours (h)",
                "Curtailment (%)",
            ]:
                if i in res.index:
                    res.at[i, c] = np.nan

        for i in [
            "Electrolyzer",
            "Derivative production",
        ]:
            if i in res.index:
                res.at[i, "Curtailment (%)"] = np.nan

    # calculate total costs:
    res.at["Total", "Cost (USD/MWh)"] = res["Cost (USD/MWh)"].sum()

    return res


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
