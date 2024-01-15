# -*- coding: utf-8 -*-
"""Functions for plotting input data and results (cost_data)."""
import json
from pathlib import Path
from typing import Literal

import graphviz
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.ptxboa_functions import (
    remove_subregions,
    select_subregions,
    subset_and_pivot_input_data,
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
        "PV tilted", "Wind Offshore", "Wind Onshore", "Wind-PV-Hybrid", "interest rate"
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
    input_data = api.get_input_data(
        scenario=st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    units = {"CAPEX": "USD/kW", "full load hours": "h/a", "interest rate": ""}

    if data_type == "interest rate":
        assert color_col == "interest rate"
        columns = "parameter_code"
        process_code = [""]
        custom_data_func_kwargs = {"float_precision": 3}
    else:
        assert color_col in [
            "PV tilted",
            "Wind Offshore",
            "Wind Onshore",
            "Wind-PV-Hybrid",
        ]
        custom_data_func_kwargs = {"float_precision": 0}
        columns = "process_code"
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
    custom_data_func_kwargs["unit"] = units[data_type]
    custom_data_func_kwargs["data_type"] = data_type
    custom_data_func_kwargs["map_variable"] = color_col

    input_data = subset_and_pivot_input_data(
        input_data=input_data,
        source_region_code=None,
        parameter_code=[data_type],
        process_code=process_code,
        index="source_region_code",
        columns=columns,
        values="value",
    )

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
    fig = px.choropleth(
        locations=df.index,
        locationmode="country names",
        color=df[color_col],
        custom_data=custom_data_func(df, **custom_data_func_kwargs),
        color_continuous_scale=agora_continuous_color_scale(),
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
    df = select_subregions(df, deep_dive_country)
    # need to calculate custom data befor is03166 column is appended.
    hover_data = custom_data_func(df, **custom_data_func_kwargs)
    # get dataframe with info about iso 3166-2 codes and map them to res_costs
    ddc_info = api.get_dimension("region")
    df["iso3166_code"] = df.index.map(
        pd.Series(ddc_info["iso3166_code"], index=ddc_info["region_name"])
    )

    geojson_file = (
        Path(__file__).parent.parent.resolve()
        / "data"
        / f"{deep_dive_country.lower().replace(' ', '_')}_subregions.geojson"
    )
    with geojson_file.open("r", encoding="utf-8") as f:
        subregion_shapes = json.load(f)

    fig = px.choropleth(
        locations=df["iso3166_code"],
        featureidkey="properties.iso_3166_2",
        color=df[color_col],
        geojson=subregion_shapes,
        custom_data=hover_data,
        color_continuous_scale=agora_continuous_color_scale(),
    )

    fig.update_geos(
        fitbounds="locations",
        visible=True,
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
        showcountries=True,  # Show country borders
        showcoastlines=True,  # Show coastlines
        countrycolor="black",  # Set default border color for other countries
        countrywidth=0.2,  # Set border width
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
            "len": 0.5,
        },  # colorbar
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
            hover = f"<b>{idx} | {data_type} </b><br><br>{row['interest rate']}"
            custom_hover_data.append(hover)
    else:
        for idx, row in df.iterrows():
            hover = f"<b>{idx} | {data_type} </b><br>"
            for i, v in zip(row.index, row):
                hover += f"<br><b>{i}</b>: {v:.{float_precision}f}{unit}"
                if i == map_variable:
                    hover += " (displayed on map)"
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
        fig.add_annotation(
            x=current_selection,
            y=1.2 * max(res_costs["Total"]),
            text="current selection",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            ax=0,
            ay=-30,
        )

    if output_unit is None:
        output_unit = st.session_state["output_unit"]

    fig.update_layout(yaxis_title=output_unit)
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


def create_process_chain_graph(api: PtxboaAPI) -> graphviz.Digraph:
    """Create graphviz graph of current process chain."""
    chain_selected = st.session_state["chain"]

    # create graph object:
    graph = graphviz.Digraph(
        graph_attr={"rankdir": "TD", "ranksep": "0.02"},
    )
    graph.attr("node", width="3.0")  # Width in inches

    def _draw_node(
        api, graph: graphviz.Digraph, process_code: str, label: str = None
    ) -> graphviz.Digraph:
        """Add node to graph."""
        chain = api.get_dimension("chain")
        process = api.get_dimension("process")
        chain_full_names = chain.replace(process["process_name"].to_dict())

        # create label:
        if label is None:
            label = chain_full_names.at[chain_selected, process_code]
        graph.node(process_code, label=label)

        # create edges for secondary input / output flows:
        input_data = api.get_input_data(st.session_state["scenario"])
        flows = input_data.loc[
            (input_data["parameter_code"] == "conversion factors")
            & (
                input_data["process_code"]
                == chain_full_names.at[chain_selected, process_code]
            ),
            ["flow_code", "value"],
        ].set_index("flow_code")
        for flow in flows.index:
            if flow == "electricity":
                graph.edge("res_gen", process_code, style="dashed")
            else:
                if flows.at[flow, "value"] < 0:
                    graph.edge(process_code, flow, style="dashed")
                else:
                    graph.edge(flow, process_code, style="dashed")

        return graph

    def _draw_edge(
        api: PtxboaAPI,
        graph: graphviz.Digraph,
        node_from: str,
        node_to: str,
        label: str = None,
    ) -> graphviz.Digraph:
        """Add edge to graph."""
        chain = api.get_dimension("chain")
        process = api.get_dimension("process")
        flow = api.get_dimension("flow")
        if label is None:
            process_code_from = chain.at[st.session_state["chain"], node_from]
            if process_code_from != "":
                flow_code = process.at[process_code_from, "main_flow_code_out"]
                label = flow.at[flow_code, "flow_name"]
        graph.edge(node_from, node_to, label=label)
        return graph

    with graph.subgraph(name="cluster_0") as sg:
        sg.node("heat")
        sg.node("water")
        sg.node("carbon dioxide")
        sg.node("bunker fuel")
        sg.attr(label="Secondary inputs / outputs")
        sg.edge("water", "heat", style="invis")
        sg.edge("heat", "carbon dioxide", style="invis")
        sg.edge("carbon dioxide", "bunker fuel", style="invis")

    with graph.subgraph(name="cluster_1") as sg_main:
        sg_main.attr(label="Main process chain")
        sg_main.node("res_gen", label=f'RE source:\n{st.session_state["res_gen"]}')
        sg_main = _draw_node(api, sg_main, "ELY")
        sg_main = _draw_node(api, sg_main, "DERIV")

        sg_main = _draw_edge(api, sg_main, "res_gen", "ELY", label="Electricity")
        sg_main = _draw_edge(api, sg_main, "ELY", "DERIV")

        if st.session_state["transport"] == "Ship":
            if st.session_state["ship_own_fuel"]:
                shiptype = "SHP-OWN"
            else:
                shiptype = "SHP"
            sg_main = _draw_node(api, sg_main, "PRE_SHP")
            sg_main = _draw_node(api, sg_main, shiptype)
            sg_main = _draw_node(api, sg_main, "POST_SHP")

            sg_main = _draw_edge(api, sg_main, "PRE_SHP", shiptype)
            sg_main = _draw_edge(api, sg_main, shiptype, "POST_SHP")
            sg_main = _draw_edge(api, sg_main, "POST_SHP", "output")

            sg_main = _draw_edge(api, sg_main, "DERIV", "PRE_SHP")

        if st.session_state["transport"] == "Pipeline":
            sg_main = _draw_node(api, sg_main, "PRE_PPL")
            sg_main = _draw_node(api, sg_main, "PPL")
            sg_main = _draw_node(api, sg_main, "POST_PPL")

            sg_main = _draw_edge(api, sg_main, "PRE_PPL", "PPL")
            sg_main = _draw_edge(api, sg_main, "PPL", "POST_PPL")
            sg_main = _draw_edge(api, sg_main, "POST_PPL", "output")

            sg_main = _draw_edge(api, sg_main, "DERIV", "PRE_PPL")

    return graph


def create_process_chain_sankey_diagram(api: PtxboaAPI):
    """Create sankey diagram of process chain."""
    # An example diagram is hard coded here.
    # It should be created based on process and chain data:
    # - show only nodes that exist in chain
    # - link width based on flows (results from calculations)

    # define nodes:
    nodes = [
        "RES-GEN",
        "ELY",
        "DERIV",
        "TRANSPORT_PRE",
        "TRANSPORT",
        "TRANSPORT_POST",
        "OUTPUT",
        "LOSSES",
        "WATER",
        "HEAT",
        "CO2",
        "BUNKER_FUEL",
        "DAC",
        "DESAL",
    ]

    def _append_link(data: dict, source: str, target: str, value: float) -> dict:
        """For sankey diagram: add link to list of links."""
        i_source = data["node"].index(source)
        i_target = data["node"].index(target)
        data["source"].append(i_source)
        data["target"].append(i_target)
        data["value"].append(value)
        return data

    data = {"node": [], "source": [], "target": [], "value": []}
    data["node"] = nodes

    # main process chain:
    data = _append_link(data, "RES-GEN", "ELY", 6)
    data = _append_link(data, "ELY", "DERIV", 5)
    data = _append_link(data, "DERIV", "TRANSPORT_PRE", 4)
    data = _append_link(data, "TRANSPORT_PRE", "TRANSPORT", 3)
    data = _append_link(data, "TRANSPORT", "TRANSPORT_POST", 2)
    data = _append_link(data, "TRANSPORT_POST", "OUTPUT", 1)

    # water:
    data = _append_link(data, "DESAL", "WATER", 0.5)
    data = _append_link(data, "WATER", "ELY", 1)
    data = _append_link(data, "DERIV", "WATER", 0.5)

    # heat:
    data = _append_link(data, "DERIV", "HEAT", 1)

    # co2:
    data = _append_link(data, "DAC", "CO2", 1)
    data = _append_link(data, "CO2", "DERIV", 1)
    data = _append_link(data, "RES-GEN", "DAC", 1)

    # bunker fuel:
    data = _append_link(data, "BUNKER_FUEL", "TRANSPORT", 1)

    # create figure:
    fig = go.Figure(
        data=go.Sankey(
            node={"label": nodes},
            link={
                "arrowlen": 15,
                "source": data["source"],
                "target": data["target"],
                "value": data["value"],
            },
        )
    )

    return fig
