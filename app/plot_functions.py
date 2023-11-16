# -*- coding: utf-8 -*-
"""Functions for plotting input data and results (cost_data)."""
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app.ptxboa_functions import remove_subregions
from ptxboa.api import PtxboaAPI


def create_world_map(api: PtxboaAPI, res_costs: pd.DataFrame):
    """Create world map."""
    parameter_to_show_on_map = "Total"

    # define title:
    title_string = (
        f"{parameter_to_show_on_map} cost of exporting"
        f"{st.session_state['chain']} to "
        f"{st.session_state['country']}"
    )
    # define color scale:
    color_scale = [
        (0, st.session_state["colors"][0]),  # Starting color at the minimum data value
        (0.5, st.session_state["colors"][6]),
        (1, st.session_state["colors"][9]),  # Ending color at the maximum data value
    ]

    # remove subregions from deep dive countries (otherwise colorscale is not correct)
    res_costs = remove_subregions(api, res_costs, st.session_state["country"])

    # Create custom hover text:
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

    # Create a choropleth world map:
    fig = px.choropleth(
        locations=res_costs.index,  # List of country codes or names
        locationmode="country names",  # Use country names as locations
        color=res_costs[parameter_to_show_on_map],  # Color values for the countries
        custom_data=[custom_hover_data],  # Pass custom data for hover information
        color_continuous_scale=color_scale,  # Choose a color scale
        title=title_string,  # set title
    )

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
        coloraxis_colorbar={"title": st.session_state["output_unit"]},  # colorbar
        margin={"t": 20, "b": 20, "l": 20, "r": 20},  # reduce margin around figure
    )

    # reduce height of the colorbar:
    fig.update_layout(coloraxis_colorbar={"len": 0.5})

    # Set the hover template to use the custom data
    fig.update_traces(hovertemplate="%{customdata}<extra></extra>")  # Custom data

    # Display the map:
    st.plotly_chart(fig, use_container_width=True)
    return


def create_bar_chart_costs(res_costs: pd.DataFrame, current_selection: str = None):
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
        color_discrete_sequence=st.session_state["colors"],
    )

    # Add the dot markers for the "total" column using plotly.graph_objects
    scatter_trace = go.Scatter(
        x=res_costs.index,
        y=res_costs["Total"],
        mode="markers+text",  # Display markers and text
        marker={"size": 10, "color": "black"},
        name="Total",
        text=res_costs["Total"].apply(
            lambda x: f"{x:.2f}"
        ),  # Use 'total' column values as text labels
        textposition="top center",  # Position of the text label above the marker
    )

    fig.add_trace(scatter_trace)

    # add highlight for current selection:
    if current_selection is not None and current_selection in res_costs.index:
        fig.add_annotation(
            x=current_selection,
            y=1.2 * res_costs.at[current_selection, "Total"],
            text="current selection",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            ax=0,
            ay=-50,
        )
    fig.update_layout(
        yaxis_title=st.session_state["output_unit"],
    )
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
