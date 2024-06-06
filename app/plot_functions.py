# -*- coding: utf-8 -*-
"""Functions for plotting input data and results (cost_data)."""
from pathlib import Path
from typing import Literal

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import pypsa
import streamlit as st

from app.ptxboa_functions import (
    get_data_type_from_input_data,
    remove_subregions,
    select_subregions,
)
from ptxboa.api import PtxboaAPI


def agora_continuous_color_scale() -> list[tuple]:
    """
    Get a continuous scale with agora colors.

    We cannot wrap this in a constant, since st.session_state["colors"] is not
    availabe during import.

    Returns
    -------
    list[tuple]
    """
    return [
        (0, st.session_state["colors"][0]),  # Starting color at the minimum data value
        (0.5, st.session_state["colors"][6]),
        (1, st.session_state["colors"][9]),  # Ending color at the maximum data value
    ]


def agora_discrete_colors_cost_categories() -> dict:
    cost_categories = [
        "Water",
        "Transportation (Ship)",
        "Electrolysis",
        "Electricity generation",
        "Electricity and H2 storage",
        "Derivate production",
        "Heat",
        "Carbon",
        # TODO: add missing category (GH #145)
    ]
    return {c: st.session_state["colors"][i] for i, c in enumerate(cost_categories)}


def plot_costs_on_map(
    api: PtxboaAPI,
    res_costs: pd.DataFrame,
    scope: Literal["world", "Argentina", "Morocco", "South Africa"] = "world",
    cost_component: str = "Total",
) -> go.Figure:
    """
    Create map for cost result data.

    Parameters
    ----------
    api : PtxboaAPI

    res_costs : pd.DataFrame
        result obtained with :func:`ptxboa_functions.calculate_results_list`
    scope : Literal["world", "Argentina", "Morocco", "South Africa"], optional
        either world or a deep dive country, by default "world"
    cost_component : str, optional
        The cost component which should be displayed as color in the map. One of
        the columns in 'res_costs', by default "Total"

    Returns
    -------
    go.Figure
    """
    if scope == "world":
        # Create a choropleth world map:
        fig = _choropleth_map_world(
            api=api,
            df=res_costs,
            color_col=cost_component,
            custom_data_func=_make_costs_hoverdata,
        )
    else:
        fig = _choropleth_map_deep_dive_country(
            api=api,
            df=res_costs,
            deep_dive_country=scope,
            color_col=cost_component,
            custom_data_func=_make_costs_hoverdata,
        )

    return _set_map_layout(fig, colorbar_title=st.session_state["output_unit"])


def plot_input_data_on_map(
    api: PtxboaAPI,
    data_type: Literal["CAPEX", "full load hours", "interest rate"],
    color_col: Literal[
        "PV tilted",
        "Wind Offshore",
        "Wind Onshore",
        "Wind Onshore (hybrid)",
        "PV tilted (hybrid)",
        "interest rate",
    ],
    scope: Literal["world", "Argentina", "Morocco", "South Africa"] = "world",
) -> go.Figure:
    """
    Plot input data on a map.

    Parameters
    ----------
    api : PtxboaAPI
    data_type : Literal["CAPEX", "full load hours", "interest rate"]
        The data type from which a parameter is plotted
    color_col : Literal[ "PV tilted", "Wind Offshore", "Wind Onshore", "Wind
        the parameter to plot on the map
    scope : Literal["world", "Argentina", "Morocco", "South Africa"], optional
        either the whole world or a deep dive country, by default "world"
    title : str, optional
        title of the figure, by default ""

    Returns
    -------
    go.Figure
    """
    input_data = get_data_type_from_input_data(api, data_type=data_type, scope=None)

    units = {"CAPEX": "USD/kW", "full load hours": "h/a", "interest rate": "%"}

    if data_type == "interest rate":
        assert color_col == "interest rate"
        custom_data_func_kwargs = {"float_precision": 2}
    if data_type == "full load hours":
        assert color_col in [
            "PV tilted",
            "Wind Offshore",
            "Wind Onshore",
            "Wind Onshore (hybrid)",
            "PV tilted (hybrid)",
        ]
        custom_data_func_kwargs = {"float_precision": 0}
    if data_type == "CAPEX":
        assert color_col in [
            "PV tilted",
            "Wind Offshore",
            "Wind Onshore",
        ]
        custom_data_func_kwargs = {"float_precision": 0}

    custom_data_func_kwargs["unit"] = units[data_type]
    custom_data_func_kwargs["data_type"] = data_type
    custom_data_func_kwargs["map_variable"] = color_col

    if scope == "world":
        # Create a choropleth world map:
        fig = _choropleth_map_world(
            api=api,
            df=input_data,
            color_col=color_col,
            custom_data_func=_make_inputs_hoverdata,
            custom_data_func_kwargs=custom_data_func_kwargs,
        )
    else:
        fig = _choropleth_map_deep_dive_country(
            api=api,
            df=input_data,
            deep_dive_country=scope,
            color_col=color_col,
            custom_data_func=_make_inputs_hoverdata,
            custom_data_func_kwargs=custom_data_func_kwargs,
        )

    return _set_map_layout(fig, colorbar_title=custom_data_func_kwargs["unit"])


def _choropleth_map_world(
    api: PtxboaAPI,
    df: pd.DataFrame,
    color_col: str,
    custom_data_func: callable,
    custom_data_func_kwargs: dict | None = None,
):
    """
    Plot a chorpleth map for the whole world and one color for each country.

    Parameters
    ----------
    df : pd.DataFrame
        wide formatted dataframe, index needs to be country or region.
    color_col : str
        column that should be displayed
    custom_data : list[pd.Series]
        custom data used for hovers

    Returns
    -------
    _type_
        _description_
    """
    if custom_data_func_kwargs is None:
        custom_data_func_kwargs = {}
    df = remove_subregions(api=api, df=df, country_name=st.session_state["country"])
    fig = px.scatter_geo(
        locations=df.index,
        locationmode="country names",
        color=df[color_col],
        custom_data=custom_data_func(df, **custom_data_func_kwargs),
        color_continuous_scale=agora_continuous_color_scale(),
        size=[15] * len(df.index),
        opacity=1,
    )
    return fig


def _choropleth_map_deep_dive_country(
    api: PtxboaAPI,
    df: pd.DataFrame,
    deep_dive_country: Literal["Argentina", "Morocco", "South Africa"],
    color_col: str,
    custom_data_func: callable,
    custom_data_func_kwargs: dict | None = None,
):
    if custom_data_func_kwargs is None:
        custom_data_func_kwargs = {}
    # subsetting 'df' for the selected deep dive country
    # missing value removal necessary for wind offshore
    df = select_subregions(df, deep_dive_country).dropna(subset=color_col)
    # need to calculate custom data befor is03166 column is appended.
    hover_data = custom_data_func(df, **custom_data_func_kwargs)
    # get dataframe with info about iso 3166-2 codes and map them to res_costs
    ddc_info = api.get_dimension("region")
    df["iso3166_code"] = df.index.map(
        pd.Series(ddc_info["iso3166_code"], index=ddc_info["region_name"])
    )
    # load representative points data
    lon_lat = pd.read_csv(
        (
            Path(__file__).parent.parent.resolve()
            / "data"
            / "subregion_representative_points.csv"
        )
    )
    # merge points to data
    df = df.merge(lon_lat, left_on="iso3166_code", right_on="iso_3166_2")

    fig = px.scatter_geo(
        lon=df["lon"],
        lat=df["lat"],
        color=df[color_col],
        custom_data=hover_data,
        color_continuous_scale=agora_continuous_color_scale(),
        size=[15] * len(df.index),
        opacity=1,
    )

    bboxes = {
        "Argentina": (-73.4154357571, -55.25, -53.628348965, -21.8323104794),
        "Morocco": (-17.0204284327, 21.4207341578, -1.12455115397, 35.7599881048),
        "South Africa": (16.3449768409, -34.8191663551, 32.830120477, -22.0913127581),
    }

    bbox = bboxes[deep_dive_country]
    pad = 3
    fig.update_geos(
        center_lon=(bbox[0] + bbox[2]) / 2.0,
        center_lat=(bbox[1] + bbox[3]) / 2.0,
        lonaxis_range=[bbox[0] - pad, bbox[2] + pad],
        lataxis_range=[bbox[1] - pad, bbox[3] + pad],
    )
    return fig


def _set_map_layout(fig: go.Figure, colorbar_title: str) -> go.Figure:
    """
    Apply a unified layout for all maps used in the app.

    The px.choropleth plotting function that creates `fig` has to be called with the
    'custom_data' argument.

    Parameters
    ----------
    fig : go.Figure
    title : str
        the figure title
    colorbar_title : str
        the title of the colorbar

    Returns
    -------
    go.Figure
        same figure with updated geos, layout and hovertemplate.
    """
    # update layout:
    fig.update_geos(
        resolution=50,
        showcountries=False,  # do not show country borders
        showcoastlines=True,  # Show coastlines
        coastlinewidth=0.2,  # coastline width
        coastlinecolor="black",  # coastline color
        showland=True,  # show land areas
        landcolor="#f3f4f5",  # Set land color to light gray
        oceancolor="#e3e4ea",  # Optionally, set ocean color slightly darker gray
        showocean=True,  # show ocean areas
        framewidth=0.2,  # width of frame around map
    )

    fig.update_layout(
        coloraxis_colorbar={
            "title": colorbar_title,
        },
        margin={"t": 20, "b": 20, "l": 20, "r": 20},  # reduce margin around figure
        height=500,
    )

    # Set the hover template to use the custom data
    fig.update_traces(hovertemplate="%{customdata}<extra></extra>")  # Custom data
    return fig


def _make_inputs_hoverdata(df, data_type, map_variable, unit, float_precision):
    custom_hover_data = []
    if data_type == "interest rate":
        for idx, row in df.iterrows():
            hover = (
                f"<b>{idx} | {data_type} </b><br><br>"
                f"{row['interest rate']:.{float_precision}f} {unit}"
            )
            custom_hover_data.append(hover)
    else:
        for idx, row in df.iterrows():
            hover = f"<b>{idx} | {data_type} </b><br>"
            for i, v in zip(row.index, row):
                hover += f"<br><b>{i}</b>: {v:.{float_precision}f} {unit}"
                if i == map_variable:
                    hover += " ← <i>displayed on map</i>"
            custom_hover_data.append(hover)
    return [custom_hover_data]


def _make_costs_hoverdata(res_costs: pd.DataFrame) -> list[pd.Series]:
    custom_hover_data = res_costs.apply(
        lambda x: f"<b>{x.name}</b><br><br>"
        + "<br>".join(
            [
                f"<b>{col}</b>: {x[col]:.1f}" f"{st.session_state['output_unit']}"
                for col in res_costs.columns[:-1]
            ]
            + [
                f"──────────<br><b>{res_costs.columns[-1]}</b>: "
                f"{x[res_costs.columns[-1]]:.1f}"
                f"{st.session_state['output_unit']}"
            ]
        ),
        axis=1,
    )
    return [custom_hover_data]


def create_bar_chart_costs(
    res_costs: pd.DataFrame,
    current_selection: str = None,
    output_unit: str | None = None,
):
    """Create bar plot for costs by components, and dots for total costs.

    Parameters
    ----------
    res_costs : pd.DataFrame
        data for plotting
    settings : dict
        settings dictionary, like output from create_sidebar()
    current_selection : str
        bar to highlight with an arrow. must be an element of res_costs.index

    Output
    ------
    fig : plotly.graph_objects.Figure
        Figure object
    """
    if res_costs.empty:  # nodata to plot (FIXME: migth not be required later)
        return go.Figure()

    fig = px.bar(
        res_costs,
        x=res_costs.index,
        y=res_costs.columns[:-1],
        height=500,
        color_discrete_map=agora_discrete_colors_cost_categories(),
    )

    # Add the dot markers for the "total" column using plotly.graph_objects
    scatter_trace = go.Scatter(
        x=res_costs.index,
        y=res_costs["Total"],
        mode="markers+text",  # Display markers and text
        marker={"size": 10, "color": "black"},
        name="Total",
        text=res_costs["Total"].apply(
            lambda x: f"{x:.0f}"
        ),  # Use 'total' column values as text labels
        textposition="top center",  # Position of the text label above the marker
    )

    fig.add_trace(scatter_trace)

    # add highlight for current selection:
    if current_selection is not None and current_selection in res_costs.index:
        if (res_costs["Total"] < 0).all():
            y = 1.2 * min(res_costs["Total"])
            ay = 30
        else:
            y = 1.2 * max(res_costs["Total"])
            ay = -30

        fig.add_annotation(
            x=current_selection,
            y=y,
            text="current selection",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            ax=0,
            ay=ay,
        )

    if output_unit is None:
        output_unit = st.session_state["output_unit"]

    fig.update_layout(yaxis_title=output_unit)
    fig.update_layout(legend_traceorder="reversed")
    return fig


def create_box_plot(res_costs: pd.DataFrame):
    """Create a subplot with one row and one column.

    Parameters
    ----------
    res_costs : pd.DataFrame
        data for plotting
    settings : dict
        settings dictionary, like output from create_sidebar()

    Output
    ------
    fig : plotly.graph_objects.Figure
        Figure object
    """
    fig = go.Figure()

    # Specify the row index of the data point you want to highlight
    highlighted_row_index = st.session_state["region"]
    # Extract the value from the specified row and column

    if highlighted_row_index:
        highlighted_value = res_costs.at[highlighted_row_index, "Total"]
    else:
        highlighted_value = 0

    # Add the box plot to the subplot
    fig.add_trace(go.Box(y=res_costs["Total"], name="Cost distribution"))

    # Add a scatter marker for the highlighted data point
    fig.add_trace(
        go.Scatter(
            x=["Cost distribution"],
            y=[highlighted_value],
            mode="markers",
            marker={"size": 10, "color": "black"},
            name=highlighted_row_index,
            text=f"Value: {highlighted_value}",  # Add a text label
        )
    )

    # Customize the layout as needed
    fig.update_layout(
        title="Cost distribution for all supply countries",
        xaxis={"title": ""},
        yaxis={"title": st.session_state["output_unit"]},
        height=500,
    )

    return fig


def create_scatter_plot(df_res, settings: dict):
    df_res["Country"] = "Other countries"
    df_res.at[st.session_state["region"], "Country"] = st.session_state["region"]

    fig = px.scatter(
        df_res,
        y="Total",
        x="tr_dst_sd",
        color="Country",
        text=df_res.index,
        color_discrete_sequence=["blue", "red"],
    )
    fig.update_traces(texttemplate="%{text}", textposition="top center")
    st.plotly_chart(fig)
    st.write(df_res)


def add_vertical_lines(fig: go.Figure):
    """Add vertical lines between periods."""
    for x in range(7 * 24, 7 * 8 * 24, 7 * 24):
        fig.add_vline(x=x, line_color="black", line_width=0.5)


def add_trace_to_figure(
    df: pd.DataFrame,
    fig: go.Figure,
    component: str,
    parameter: str,
    color: str,
    fill: bool = False,
):
    """Add line (trace) to profile figure."""
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


def prepare_data_for_profile_figures(n: pypsa.Network) -> pd.DataFrame:
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

    return df_sel


def create_profile_figure_generation(df_sel: pd.DataFrame) -> go.Figure:
    """Create generation profile figure."""
    fig = go.Figure()

    add_trace_to_figure(
        df_sel, fig, component="PV tilted", parameter="Power", fill=True, color="yellow"
    )
    add_trace_to_figure(
        df_sel,
        fig,
        component="Wind onshore",
        parameter="Power",
        fill=True,
        color="blue",
    )
    add_trace_to_figure(
        df_sel,
        fig,
        component="Wind offshore",
        parameter="Power",
        fill=True,
        color="blue",
    )
    add_trace_to_figure(
        df_sel, fig, component="Electrolyzer", parameter="Power", color="black"
    )
    add_trace_to_figure(
        df_sel, fig, component="Derivate production", parameter="Power", color="red"
    )

    add_vertical_lines(fig)

    fig.update_layout(
        xaxis={"title": "time (h)"},
        yaxis={"title": "output (MW)"},
    )

    return fig


def create_profile_figure_soc(df_sel: pd.DataFrame) -> go.Figure:
    """Create storage state of charge figure."""
    include_final_product_storage = st.toggle("Show final product storage", value=False)
    # storage figure:
    fig = go.Figure()

    add_trace_to_figure(
        df_sel,
        fig,
        component="Electricity storage",
        parameter="Power",
        color="black",
    )

    add_trace_to_figure(
        df_sel,
        fig,
        component="H2 storage",
        parameter="Power",
        color="red",
    )
    if include_final_product_storage:
        add_trace_to_figure(
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

    return fig


def create_profile_figure_capacity_factors(df_sel: pd.DataFrame) -> go.Figure:
    """Create capacity factors profile figure."""
    fig = go.Figure()
    add_trace_to_figure(
        df_sel, fig, component="PV tilted", parameter="cap. factor", color="yellow"
    )
    add_trace_to_figure(
        df_sel,
        fig,
        component="Wind onshore",
        parameter="cap. factor",
        color="blue",
    )
    add_trace_to_figure(
        df_sel,
        fig,
        component="Wind offshore",
        parameter="cap. factor",
        color="blue",
    )
    add_vertical_lines(fig)

    return fig
