# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""
from urllib.parse import urlparse

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ptxboa.api import PtxboaAPI


@st.cache_data()
def calculate_results_single(_api: PtxboaAPI, settings: dict) -> pd.DataFrame:
    """Calculate results for a single set of settings.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.

    Returns
    -------
    pd.DataFrame
        same format as for :meth:`~ptxboa.api.PtxboaAPI.calculate()`
    """
    res = _api.calculate(**settings)

    return res


def calculate_results(
    api: PtxboaAPI, settings: dict, region_list: list = None
) -> pd.DataFrame:
    """Calculate results for source regions and one selected target country.

    TODO: This function will eventually be replaced by ``calculate_results_list()``.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.
    region_list : list or None
        The regions for which the results are calculated. If None, all regions
        available in the API will be used.

    Returns
    -------
    pd.DataFrame
        same format as for :meth:`~ptxboa.api.PtxboaAPI.calculate()`
    """
    res_list = []

    if region_list is None:
        region_list = api.get_dimension("region")["region_name"]

    for region in region_list:
        settings2 = settings.copy()
        settings2["region"] = region
        res_single = calculate_results_single(api, settings2)
        res_list.append(res_single)
    res = pd.concat(res_list)
    return res


def calculate_results_list(
    api: PtxboaAPI,
    settings: dict,
    parameter_to_change: str,
    parameter_list: list = None,
) -> pd.DataFrame:
    """Calculate results for source regions and one selected target country.

    Parameters
    ----------
    _api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.
    parameter_to_change : str
        element of settings for which a list of values is to be used.
    parameter_list : list or None
        The values of ``parameter_to_change`` for which the results are calculated.
        If None, all values available in the API will be used.

    Returns
    -------
    pd.DataFrame
        same format as for :meth:`~ptxboa.api.PtxboaAPI.calculate()`
    """
    res_list = []

    if parameter_list is None:
        parameter_list = api.get_dimension(parameter_to_change).index

    for parameter in parameter_list:
        settings2 = settings.copy()
        settings2[parameter_to_change] = parameter
        res_single = calculate_results_single(api, settings2)
        res_list.append(res_single)
    res_details = pd.concat(res_list)

    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index=parameter_to_change,
        columns="process_type",
        values="values",
        aggfunc="sum",
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    return res


@st.cache_data()
def aggregate_costs(res_details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detailed costs.

    TODO: This function will eventually be replaced by ``calculate_results_list``
    """
    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index="region", columns="process_type", values="values", aggfunc="sum"
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    return res


# Settings:
def create_sidebar(api: PtxboaAPI):
    st.sidebar.subheader("Main settings:")
    settings = {}
    include_subregions = False
    if include_subregions:
        region_list = api.get_dimension("region").index
    else:
        region_list = (
            api.get_dimension("region")
            .loc[api.get_dimension("region")["subregion_code"] == ""]
            .index
        )

    settings["region"] = st.sidebar.selectbox(
        "Supply country / region:",
        region_list,
        help=(
            "One supply country or region can be selected here, "
            " and detailed settings can be selected for this region below "
            "(RE source, mode of transportation). For other regions, "
            "default settings will be used."
        ),
    )
    include_subregions = st.sidebar.toggle(
        "Include subregions",
        help=(
            "For three deep-dive countries (Argentina, Morocco, and South Africa) "
            "the app calculates costs for subregions as well. Activate this switch"
            "if you want to chose one of these subregions as a supply region. "
        ),
    )
    settings["country"] = st.sidebar.selectbox(
        "Demand country:",
        api.get_dimension("country").index,
        help=(
            "The country you aim to export to. Some key info on the demand country you "
            "choose here are displayed in the info box."
        ),
    )
    # get chain as combination of product, electrolyzer type and reconversion option:
    c1, c2 = st.sidebar.columns(2)
    with c1:
        product = st.selectbox(
            "Product:",
            [
                "Ammonia",
                "Green Iron",
                "Hydrogen",
                "LOHC",
                "Methane",
                "Methanol",
                "Ft e-fuels",
            ],
            help="The product you want to export.",
        )
    with c2:
        ely = st.selectbox(
            "Electrolyzer type:",
            [
                "AEL",
                "PEM",
                "SEOC",
            ],
            help="The electrolyzer type you wish to use.",
        )
    if product in ["Ammonia", "Methane"]:
        use_reconversion = st.sidebar.toggle(
            "Include reconversion to H2",
            help=(
                "If activated, account for costs of "
                "reconverting product to H2 in demand country."
            ),
        )
    else:
        use_reconversion = False

    settings["chain"] = f"{product} ({ely})"
    if use_reconversion:
        settings["chain"] = f"{settings['chain']} + reconv. to H2"

    settings["res_gen"] = st.sidebar.selectbox(
        "Renewable electricity source (for selected supply region):",
        api.get_dimension("res_gen").index,
        help=(
            "The source of electricity for the selected source country. For all "
            "other countries Wind-PV hybrid systems will be used (an optimized mixture "
            "of PV and wind onshore plants)"
        ),
    )

    # get scenario as combination of year and cost assumption:
    c1, c2 = st.sidebar.columns(2)
    with c1:
        data_year = st.radio(
            "Data year:",
            [2030, 2040],
            index=1,
            help=(
                "To cover parameter uncertainty and development over time, we provide "
                "cost reduction pathways (high / medium / low) for 2030 and 2040."
            ),
            horizontal=True,
        )
    with c2:
        cost_scenario = st.radio(
            "Cost assumptions:",
            ["high", "medium", "low"],
            index=1,
            help=(
                "To cover parameter uncertainty and development over time, we provide "
                "cost reduction pathways (high / medium / low) for 2030 and 2040."
            ),
            horizontal=True,
        )
    settings["scenario"] = f"{data_year} ({cost_scenario})"

    st.sidebar.subheader("Additional settings:")
    settings["secproc_co2"] = st.sidebar.radio(
        "Carbon source:",
        api.get_dimension("secproc_co2").index,
        horizontal=True,
        help="Help text",
    )
    settings["secproc_water"] = st.sidebar.radio(
        "Water source:",
        api.get_dimension("secproc_water").index,
        horizontal=True,
        help="Help text",
    )
    settings["transport"] = st.sidebar.radio(
        "Mode of transportation (for selected supply country):",
        api.get_dimension("transport").index,
        horizontal=True,
        help="Help text",
    )
    if settings["transport"] == "Ship":
        settings["ship_own_fuel"] = st.sidebar.toggle(
            "For shipping option: Use the product as own fuel?",
            help="Help text",
        )
    settings["output_unit"] = st.sidebar.radio(
        "Unit for delivered costs:",
        api.get_dimension("output_unit").index,
        horizontal=True,
        help="Help text",
    )

    st.sidebar.toggle(
        "Edit input data",
        help="""Activate this to enable editing of input data.
Currently, your changes will be stored, but they will not be
used in calculation and they will not be displayed in figures.

Disable this setting to reset user data to default values.""",
        value=False,
        key="edit_input_data",
    )

    if st.session_state["edit_input_data"] is False:
        reset_user_changes()

    # import agora color scale:
    if "colors" not in st.session_state:
        colors = pd.read_csv("data/Agora_Industry_Colours.csv")
        st.session_state["colors"] = colors["Hex Code"].to_list()
    return settings


def create_world_map(settings: dict, res_costs: pd.DataFrame):
    """Create world map."""
    parameter_to_show_on_map = "Total"

    # define title:
    title_string = (
        f"{parameter_to_show_on_map} cost of exporting {settings['chain']} to "
        f"{settings['country']}"
    )
    # define color scale:
    color_scale = [
        (0, st.session_state["colors"][0]),  # Starting color at the minimum data value
        (0.5, st.session_state["colors"][6]),
        (1, st.session_state["colors"][9]),  # Ending color at the maximum data value
    ]

    # Create custom hover text:
    custom_hover_data = res_costs.apply(
        lambda x: f"<b>{x.name}</b><br><br>"
        + "<br>".join(
            [
                f"<b>{col}</b>: {x[col]:.1f} {settings['output_unit']}"
                for col in res_costs.columns[:-1]
            ]
            + [
                f"──────────<br><b>{res_costs.columns[-1]}</b>: "
                f"{x[res_costs.columns[-1]]:.1f} {settings['output_unit']}"
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
        coloraxis_colorbar={"title": settings["output_unit"]},  # colorbar
        height=600,  # height of figure
        margin={"t": 20, "b": 20, "l": 20, "r": 20},  # reduce margin around figure
    )

    # Set the hover template to use the custom data
    fig.update_traces(hovertemplate="%{customdata}<extra></extra>")  # Custom data

    # Display the map:
    st.plotly_chart(fig, use_container_width=True)
    return


def create_bar_chart_costs(
    res_costs: pd.DataFrame, settings: dict, current_selection: str = None
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
    """
    if res_costs.empty:  # nodata to plot (FIXME: migth not be required later)
        return

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
        yaxis_title=settings["output_unit"],
    )
    st.plotly_chart(fig, use_container_width=True)


def create_box_plot(res_costs: pd.DataFrame, settings: dict):
    # Create a subplot with one row and one column
    fig = go.Figure()

    # Specify the row index of the data point you want to highlight
    highlighted_row_index = settings["region"]
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
        yaxis={"title": settings["output_unit"]},
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_scatter_plot(df_res, settings: dict):
    df_res["Country"] = "Other countries"
    df_res.at[settings["region"], "Country"] = settings["region"]

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


def content_dashboard(api, res_costs: dict, context_data: dict, settings: pd.DataFrame):
    with st.expander("What is this?"):
        st.markdown(
            """
This is the dashboard. It shows key results according to your settings:
- a map and a box plot that show the spread and the
regional distribution of total costs across supply regions
- a split-up of costs by category for your chosen supply region
- key information on your chosen demand country.

Switch to other tabs to explore data and results in more detail!
            """
        )

    c_1, c_2 = st.columns([2, 1])
    with c_2:
        create_infobox(context_data, settings)

    with c_1:
        create_world_map(settings, res_costs)

    st.divider()

    c_3, c_4 = st.columns(2)

    with c_3:
        create_box_plot(res_costs, settings)
    with c_4:
        filtered_data = res_costs[res_costs.index == settings["region"]]
        create_bar_chart_costs(filtered_data, settings)

    st.write("Chosen settings:")
    st.write(settings)


def content_market_scanning(
    api: PtxboaAPI, res_costs: pd.DataFrame, settings: dict
) -> None:
    """Create content for the "market scanning" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.
    res_costs : pd.DataFrame
        Results.
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Market scanning: Get an overview of competing PTX BOA supply countries
 and potential demand countries.**

This sheet helps you to better evaluate your country's competitive position
 as well as your options on the emerging global H2 market.

            """
        )

    # get input data:
    input_data = api.get_input_data(settings["scenario"])

    # filter shipping and pipeline distances:
    distances = input_data.loc[
        (input_data["parameter_code"].isin(["shipping distance", "pipeline distance"]))
        & (input_data["target_country_code"] == settings["country"]),
        ["source_region_code", "parameter_code", "value"],
    ]
    distances = distances.pivot_table(
        index="source_region_code",
        columns="parameter_code",
        values="value",
        aggfunc="sum",
    )

    # merge costs and distances:
    df_plot = pd.DataFrame()
    df_plot["total costs"] = res_costs["Total"]
    df_plot = df_plot.merge(distances, left_index=True, right_index=True)

    # do not show subregions:
    df_plot = remove_subregions(api, df_plot, settings)

    # create plot:
    [c1, c2] = st.columns([1, 5])
    with c1:
        # select which distance to show:
        selected_distance = st.radio(
            "Select parameter:",
            ["shipping distance", "pipeline distance"],
        )
    with c2:
        fig = px.scatter(
            df_plot,
            x=selected_distance,
            y="total costs",
            title="Costs and transportation distances",
            height=600,
        )
        # Add text above markers
        fig.update_traces(
            text=df_plot.index,
            textposition="top center",
            mode="markers+text",
        )

        st.plotly_chart(fig)

    # show data in tabular form:
    st.markdown("**Data:**")
    column_config = config_number_columns(df_plot, format="%.1f")
    st.dataframe(df_plot, use_container_width=True, column_config=column_config)


def remove_subregions(api: PtxboaAPI, df: pd.DataFrame, settings: dict):
    """Remove subregions from a dataframe.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    df : pandas DataFrame with list of regions as index.

    Returns
    -------
    pandas DataFrame with subregions removed from index.
    """
    # do not show subregions:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )

    # ensure that target country is not in list of regions:
    if settings["country"] in region_list_without_subregions:
        region_list_without_subregions.remove(settings["country"])

    df = df.loc[region_list_without_subregions]

    return df


def content_compare_costs(
    api: PtxboaAPI, res_costs: pd.DataFrame, settings: dict
) -> None:
    """Create content for the "compare costs" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Compare costs**

On this sheet, users can analyze total cost and cost components for
different supply countries, scenarios, renewable electricity sources and process chains.
Data is represented as a bar chart and in tabular form.

Data can be filterend and sorted.
            """
        )

    def display_costs(
        df_costs: pd.DataFrame, key: str, titlestring: str, settings: dict
    ):
        """Display costs as table and bar chart."""
        st.subheader(titlestring)
        c1, c2 = st.columns([1, 5])
        with c1:
            # filter data:
            df_res = df_costs.copy()

            # select filter:
            show_which_data = st.radio(
                "Select elements to display:",
                ["All", "Manual select"],
                index=0,
                key=f"show_which_data_{key}",
            )

            # apply filter:
            if show_which_data == "Manual select":
                ind_select = st.multiselect(
                    "Select regions:",
                    df_res.index.values,
                    default=df_res.index.values,
                    key=f"select_data_{key}",
                )
                df_res = df_res.loc[ind_select]

            # sort:
            sort_ascending = st.toggle(
                "Sort by total costs?", value=True, key=f"sort_data_{key}"
            )
            if sort_ascending:
                df_res = df_res.sort_values(["Total"], ascending=True)
        with c2:
            # create graph:
            create_bar_chart_costs(df_res, settings, current_selection=settings[key])

        with st.expander("**Data**"):
            column_config = config_number_columns(
                df_res, format=f"%.1f {settings['output_unit']}"
            )
            st.dataframe(df_res, use_container_width=True, column_config=column_config)

    res_costs_without_subregions = remove_subregions(api, res_costs, settings)
    display_costs(res_costs_without_subregions, "region", "Costs by region:", settings)

    # Display costs by scenario:
    res_scenario = calculate_results_list(api, settings, "scenario")
    display_costs(res_scenario, "scenario", "Costs by data scenario:", settings)

    # Display costs by RE generation:
    # TODO: remove PV tracking manually, this needs to be fixed in data
    list_res_gen = api.get_dimension("res_gen").index.to_list()
    list_res_gen.remove("PV tracking")
    res_res_gen = calculate_results_list(
        api, settings, "res_gen", parameter_list=list_res_gen
    )
    display_costs(
        res_res_gen, "res_gen", "Costs by renewable electricity source:", settings
    )

    # TODO: display costs by chain


def content_deep_dive_countries(
    api: PtxboaAPI, res_costs: pd.DataFrame, settings: dict
) -> None:
    """Create content for the "costs by region" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Deep-dive countries: Data on country and regional level**

For the three deep-dive countries (Argentina, Morocco and South Africa)
this tab shows full load hours of renewable generation and total costs
in regional details.

The box plots show median, 1st and 3rd quartile as well as the total spread of values.
They also show the data for your selected supply country or region for comparison.
            """
        )

    st.markdown("TODO: add country map")

    ddc = st.radio(
        "Select country:", ["Argentina", "Morocco", "South Africa"], horizontal=True
    )

    # get input data:

    input_data = api.get_input_data(settings["scenario"])

    # filter data:
    # get list of subregions:
    region_list = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["region_name"].str.startswith(ddc)]
        .index.to_list()
    )

    # TODO: implement display of total costs
    list_data_types = ["full load hours"]
    data_selection = st.radio(
        "Select data type",
        list_data_types,
        horizontal=True,
        key="sel_data_ddc",
    )
    if data_selection == "full load hours":
        parameter_code = ["full load hours"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        x = "process_code"
        column_config = {"format": "%.0f h/a", "min_value": 0, "max_value": 8760}

    if data_selection == "total costs":
        df = res_costs.copy()
        df = res_costs.loc[region_list].rename({"Total": data_selection}, axis=1)
        df = df.rename_axis("source_region_code", axis=0)
        x = None
        st.markdown("TODO: fix surplus countries in data table")

    c1, c2 = st.columns(2, gap="medium")
    with c2:
        # show data:
        st.markdown("**Data:**")
        df = display_and_edit_data_table(
            input_data=input_data,
            columns=x,
            source_region_code=region_list,
            parameter_code=parameter_code,
            process_code=process_code,
            column_config=column_config,
            key_suffix="_ddc",
        )
    with c1:
        # create plot:
        st.markdown("**Figure:**")
        fig = px.box(df)
        st.plotly_chart(fig, use_container_width=True)


def content_input_data(api: PtxboaAPI, settings: dict) -> None:
    """Create content for the "input data" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    settings : dict
        settings from the streamlit app. An example can be obtained with the
        return value from :func:`ptxboa_functions.create_sidebar`.

    Output
    ------
    None
    """
    with st.expander("What is this?"):
        st.markdown(
            """
**Input data**

This tab gives you an overview of model input data that is country-specific.
This includes full load hours (FLH) and capital expenditures (CAPEX)
of renewable generation technologies, weighted average cost of capital (WACC),
as well as shipping and pipeline distances to the chosen demand country.
The box plots show median, 1st and 3rd quartile as well as the total spread of values.
They also show the data for your country for comparison.
            """
        )

    # get input data:
    input_data = api.get_input_data(
        settings["scenario"], user_data=st.session_state["user_changes_df"]
    )

    # filter data:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )
    input_data = input_data.loc[
        input_data["source_region_code"].isin(region_list_without_subregions)
    ]

    list_data_types = ["CAPEX", "full load hours", "interest rate"]
    data_selection = st.radio("Select data type", list_data_types, horizontal=True)
    if data_selection == "CAPEX":
        parameter_code = ["CAPEX"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        x = "process_code"
        column_config = {"format": "%.0f USD/kW", "min_value": 0}

    if data_selection == "full load hours":
        parameter_code = ["full load hours"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        x = "process_code"
        column_config = {"format": "%.0f h/a", "min_value": 0, "max_value": 8760}

    if data_selection == "interest rate":
        parameter_code = ["interest rate"]
        process_code = [""]
        x = "parameter_code"
        column_config = {"format": "%.3f", "min_value": 0, "max_value": 1}

    c1, c2 = st.columns(2, gap="medium")
    with c2:
        # show data:
        st.markdown("**Data:**")
        df = display_and_edit_data_table(
            input_data=input_data,
            columns=x,
            source_region_code=region_list_without_subregions,
            parameter_code=parameter_code,
            process_code=process_code,
            column_config=column_config,
        )

    with c1:
        # create plot:
        st.markdown("**Figure:**")
        fig = px.box(df)
        st.plotly_chart(fig, use_container_width=True)

    display_user_changes()
    st.write(st.session_state)


def reset_user_changes():
    """Reset all user changes."""
    if st.session_state["user_changes_df"] is not None:
        st.session_state["user_changes_df"] = None


def display_user_changes():
    """Display input data changes made by user."""
    if st.session_state["user_changes_df"] is not None:
        st.write("**Input data has been modified:**")
        st.dataframe(
            st.session_state["user_changes_df"].style.format(precision=3),
            hide_index=True,
        )


def display_and_edit_data_table(
    input_data: pd.DataFrame,
    source_region_code: list,
    parameter_code: list,
    process_code: list,
    index: str = "source_region_code",
    columns: str = "process_code",
    values: str = "value",
    column_config: dict = None,
    key_suffix: str = "",
) -> pd.DataFrame:
    """Display selected input data as 2D table, which can also be edited."""
    ind1 = input_data["source_region_code"].isin(source_region_code)
    ind2 = input_data["parameter_code"].isin(parameter_code)
    ind3 = input_data["process_code"].isin(process_code)
    df = input_data.loc[ind1 & ind2 & ind3]
    df_tab = df.pivot_table(index=index, columns=columns, values=values, aggfunc="sum")

    # if editing is enabled, store modifications in session_state:
    if st.session_state["edit_input_data"]:
        disabled = [index]
        key = (
            f"edit_input_data_{'_'.join(parameter_code).replace(' ', '_')}{key_suffix}"
        )
    else:
        disabled = True
        key = None

    # configure columns for display:
    if column_config is None:
        column_config_all = None
    else:
        column_config_all = config_number_columns(df_tab, **column_config)

    # display data:
    st.data_editor(
        df_tab,
        use_container_width=True,
        key=key,
        num_rows="fixed",
        disabled=disabled,
        column_config=column_config_all,
        on_change=register_user_changes,
        kwargs={
            "parameter_code": parameter_code,
            "index": index,
            "columns": columns,
            "values": values,
            "df_tab": df_tab,
            "key": key,
        },
    )
    if st.session_state["edit_input_data"]:
        st.markdown("You can edit data directly in the table!")
    return df_tab


def register_user_changes(parameter_code, index, columns, values, df_tab, key):
    """
    Register all user changes in the session state variable "user_changes_df".

    If a change already has been recorded, use the lastest value.
    """
    # convert session state dict to dataframe:
    # Create a list of dictionaries
    data_dict = st.session_state[key]["edited_rows"]
    data_list = []

    for k, v in data_dict.items():
        for c_name, value in v.items():
            data_list.append({index: k, columns: c_name, values: value})

        # Convert the list to a DataFrame
    res = pd.DataFrame(data_list)
    res["parameter_code"] = parameter_code[0]

    # Replace the 'id' values with the corresponding index elements from df_tab
    res[index] = res[index].map(lambda x: df_tab.index[x])

    if st.session_state["user_changes_df"] is None:
        st.session_state["user_changes_df"] = pd.DataFrame(
            columns=["source_region_code", "process_code", "parameter_code", "value"]
        )

    # only track the last changes if a duplicate entry is found.
    st.session_state["user_changes_df"] = pd.concat(
        [st.session_state["user_changes_df"], res]
    ).drop_duplicates(
        subset=["source_region_code", "process_code", "parameter_code"], keep="last"
    )


def create_infobox(context_data: dict, settings: dict):
    data = context_data["infobox"]
    st.markdown(f"**Key information on {settings['country']}:**")
    demand = data.at[settings["country"], "Projected H2 demand [2030]"]
    info1 = data.at[settings["country"], "key_info_1"]
    info2 = data.at[settings["country"], "key_info_2"]
    info3 = data.at[settings["country"], "key_info_3"]
    info4 = data.at[settings["country"], "key_info_4"]
    st.markdown(f"* Projected H2 demand in 2030: {demand}")

    def write_info(info):
        if isinstance(info, str):
            st.markdown(f"* {info}")

    write_info(info1)
    write_info(info2)
    write_info(info3)
    write_info(info4)


def import_context_data():
    """Import context data from excel file."""
    filename = "data/context_data.xlsx"
    cd = {}
    cd["demand_countries"] = pd.read_excel(
        filename, sheet_name="demand_countries", skiprows=1
    )
    cd["certification_schemes_countries"] = pd.read_excel(
        filename, sheet_name="certification_schemes_countries"
    )
    cd["certification_schemes"] = pd.read_excel(
        filename, sheet_name="certification_schemes", skiprows=1
    )
    cd["sustainability"] = pd.read_excel(filename, sheet_name="sustainability")
    cd["supply"] = pd.read_excel(filename, sheet_name="supply", skiprows=1)
    cd["literature"] = pd.read_excel(filename, sheet_name="literature")
    cd["infobox"] = pd.read_excel(
        filename,
        sheet_name="infobox",
        usecols="A:F",
        skiprows=1,
    ).set_index("country_name")
    return cd


def create_fact_sheet_demand_country(context_data: dict, country_name: str):
    with st.expander("What is this?"):
        st.markdown(
            """
**Country fact sheets**

This sheet provides you with additional information on the production and import of
 hydrogen and derivatives in all PTX BOA supply and demand countries.
For each selected supply and demand country pair, you will find detailed
 country profiles.

 For demand countries, we cover the following aspects:
 country-specific projected hydrogen demand,
 target sectors for hydrogen use,
 hydrogen-relevant policies and competent authorities,
 certification and regulatory frameworks,
 and country-specific characteristics as defined in the demand countries'
 hydrogen strategies.

 For the supplying countries, we cover the country-specific technical potential
 for renewables (based on various data sources),
 LNG export and import infrastructure,
 CCS potentials,
 availability of an H2 strategy
 and wholesale electricity prices.
            """
        )
    df = context_data["demand_countries"]
    data = df.loc[df["country_name"] == country_name].iloc[0].to_dict()

    flags_to_country_names = {
        "France": ":flag-fr:",
        "Germany": ":flag-de:",
        "Netherlands": ":flag-nl:",
        "Spain": ":flag-es:",
        "China": ":flag-cn:",
        "India": ":flag-in:",
        "Japan": ":flag-jp:",
        "South Korea": ":flag-kr:",
        "USA": ":flag-us:",
    }

    st.subheader(
        f"{flags_to_country_names[country_name]} Fact sheet for {country_name}"
    )
    with st.expander("**Demand**"):
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("**Projected H2 demand in 2030:**")
            st.markdown(data["h2_demand_2030"])
            st.markdown(f"*Source: {data['source_h2_demand_2030']}*")
        with c2:
            st.markdown("**Targeted sectors (main):**")
            st.markdown(data["demand_targeted_sectors_main"])
            st.markdown(f"*Source: {data['source_targeted_sectors_main']}*")
        with c3:
            st.markdown("**Targeted sectors (secondary):**")
            st.markdown(data["demand_targeted_sectors_secondary"])
            st.markdown(f"*Source: {data['source_targeted_sectors_secondary']}*")

    with st.expander("**Hydrogen strategy**"):
        st.markdown("**Documents:**")
        st.markdown(data["h2_strategy_documents"])

        st.markdown("**Authorities:**")
        st.markdown(data["h2_strategy_authorities"])

    with st.expander("**Hydrogen trade characteristics**"):
        st.markdown(data["h2_trade_characteristics"])
        st.markdown(f"*Source: {data['source_h2_trade_characteristics']}*")

    with st.expander("**Infrastructure**"):
        st.markdown("**LNG import terminals:**")
        st.markdown(data["lng_import_terminals"])
        st.markdown(f"*Source: {data['source_lng_import_terminals']}*")

        st.markdown("**H2 pipeline projects:**")
        st.markdown(data["h2_pipeline_projects"])
        st.markdown(f"*Source: {data['source_h2_pipeline_projects']}*")

    if data["certification_info"] != "":
        with st.expander("**Certification schemes**"):
            st.markdown(data["certification_info"])
            st.markdown(f"*Source: {data['source_certification_info']}*")


def create_fact_sheet_supply_country(context_data: dict, country_name: str):
    """Display information on a chosen supply country."""
    df = context_data["supply"]
    data = df.loc[df["country_name"] == country_name].iloc[0].to_dict()

    st.subheader(f"Fact sheet for {country_name}")
    text = (
        "**Technical potential for renewable electricity generation:**\n"
        f"- {data['source_re_tech_pot_EWI']}: "
        f"\t{data['re_tech_pot_EWI']:.0f} TWh/a\n"
        f"- {data['source_re_tech_pot_PTXAtlas']}: "
        f"\t{data['re_tech_pot_PTXAtlas']:.0f} TWh/a\n"
    )

    st.markdown(text)

    text = (
        "**LNG infrastructure:**\n"
        f"- {data['lng_export']} export terminals\n"
        f"- {data['lng_import']} import terminals.\n\n"
        f"*Source: {data['source_lng']}*"
    )

    st.markdown(text)

    st.write("TODO: CCS pot, elec prices, H2 strategy")


def create_fact_sheet_certification_schemes(context_data: dict):
    with st.expander("What is this?"):
        st.markdown(
            """
**Get supplementary information on H2-relevant certification frameworks**

This sheet provides you with an overview of current governmental regulations
and voluntary standards for H2 products.
            """
        )
    df = context_data["certification_schemes"]
    helptext = "Select the certification scheme you want to know more about."
    scheme_name = st.selectbox("Select scheme:", df["name"], help=helptext)
    data = df.loc[df["name"] == scheme_name].iloc[0].to_dict()

    # replace na with "not specified":
    for key in data:
        if data[key] is np.nan:
            data[key] = "not specified"

    st.markdown(data["description"])

    with st.expander("**Characteristics**"):
        st.markdown(
            f"- **Relation to other standards:** {data['relation_to_other_standards']}"
        )
        st.markdown(f"- **Geographic scope:** {data['geographic_scope']}")
        st.markdown(f"- **PTXBOA demand countries:** {data['ptxboa_demand_countries']}")
        st.markdown(f"- **Labels:** {data['label']}")
        st.markdown(f"- **Lifecycle scope:** {data['lifecycle_scope']}")

        st.markdown(
            """
**Explanations:**

- Info on "Geographical scope":
  - This field provides an answer to the question: if you want to address a specific
 country of demand, which regulations and/or standards exist in this country
   that require or allow proof of a specific product property?
- Info on "Lifecycle scope":
  - Well-to-gate: GHG emissions are calculated up to production.
  - Well-to-wheel: GHG emissions are calculated up to the time of use.
  - Further information on the life cycle scopes can be found in
IRENA & RMI (2023): Creating a global hydrogen market: certification to enable trade,
 pp. 15-19
"""
        )

    with st.expander("**Scope**"):
        if data["scope_emissions"] != "not specified":
            st.markdown("- **Emissions:**")
            st.markdown(data["scope_emissions"])

        if data["scope_electricity"] != "not specified":
            st.markdown("- **Electricity:**")
            st.markdown(data["scope_electricity"])

        if data["scope_water"] != "not specified":
            st.markdown("- **Water:**")
            st.markdown(data["scope_water"])

        if data["scope_biodiversity"] != "not specified":
            st.markdown("- **Biodiversity:**")
            st.markdown(data["scope_biodiversity"])

        if data["scope_other"] != "not specified":
            st.markdown("- **Other:**")
            st.markdown(data["scope_other"])

    with st.expander("**Sources**"):
        st.markdown(data["sources"])


def create_content_sustainability(context_data: dict):
    with st.expander("What is this?"):
        st.markdown(
            """
**Get supplementary information on PTX-relevant sustainability issues**

Hydrogen is not sustainable by nature.
And sustainability goes far beyond the CO2-footprint of a product.
It also includes other environmental as well as socio-economic dimensions.

This is why we provide you with a set of questions that will help you assess your plans
for PTX production and export from a comprehensive sustainability perspective.
Please note that this list does not claim to be exhaustive,
but only serves for an orientation on the topic.
            """
        )
    df = context_data["sustainability"]

    c1, c2 = st.columns([2, 1])
    with c1:
        st.image("static/sustainability.png")
        captiontext = (
            "Source: https://ptx-hub.org/wp-content/uploads/2022/05/"
            "PtX-Hub-PtX.Sustainability-Dimensions-and-Concerns-Scoping-Paper.pdf"
        )
        st.caption(captiontext)
    with c2:
        st.markdown(
            """
**Dimensions of sustainability**

**What sustainability aspects should be considered for PTX products,
 production and policies?**

**What questions should be asked before and during project development?**

In this tab we aim to provide a basic approach to these questions.
 To the left, you can see the framework along which the compilation
 of sustainability aspects in this tab is structured. It is based on the EESG framework
 as elaborated by the PtX Hub and sustainability criteria developed by the Öko-Institut.

**The framework distinguishes four key sustainability dimensions - Environmental,
 Economic, Social and Governance - from which you can select below.**

 Within each of these dimensions there are different clusters of sustainability aspects
 that we address in a set of questions. We differentiate between questions indicating
 guardrails and questions suggesting goals.

With this compilation, we aim to provide a general overview of the sustainability
 issues that may be relevant in the context of PTX production. Of course,
 different aspects are more or less important depending on the project,
 product and country.

**Take a look for yourself to see which dimensions are most important
 from where you are coming from.**
                    """
        )
    st.divider()

    c1, c2 = st.columns(2)
    with c1:
        helptext = "helptext"
        dimension = st.selectbox(
            "Select dimension:", df["dimension"].unique(), help=helptext
        )
    with c2:
        helptext = """
We understand **guardrails** as guidelines which can help you to produce green
PTX products that are sustainable also beyond their greenhouse gas emission intensity.

**Goals** are guidelines which can help link PTX production to improving local
 ecological and socio-economic circumstances in the supply country.
They act as additional to guardrails which should be fulfilled in the first place
 to meet basic sustainability needs.
"""
        question_type = st.radio(
            "Guardrails or goals?",
            ["Guardrails", "Goals"],
            help=helptext,
            horizontal=True,
        )
        data = df.loc[(df["dimension"] == dimension) & (df["type"] == question_type)]

    for topic in data["topic"].unique():
        with st.expander(f"**{topic}**"):
            data_select = data.loc[data["topic"] == topic]
            for _ind, row in data_select.iterrows():
                st.markdown(f"- {row['question']}")


def is_valid_url(url: str) -> bool:
    """Check if a string is a valid url."""
    if not isinstance(url, str):
        return False

    try:
        result = urlparse(url)
        # Check if result.scheme and result.netloc are non-empty
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def create_content_literature(context_data: dict):
    with st.expander("What is this?"):
        st.markdown(
            """
**List of references**

This tab contains a list of references used in this app.
            """
        )
    df = context_data["literature"]
    markdown_text = ""
    for _ind, row in df.iterrows():
        if is_valid_url(row["url"]):
            text = f"- {row['long_name']}: [Link]({row['url']})\n"
        else:
            text = f"- {row['long_name']}\n"
        markdown_text = markdown_text + text

    st.markdown(markdown_text)


def content_disclaimer():
    with st.expander("What is this?"):
        st.markdown(
            """
**Disclaimer**

Information on product details of the PTX Business Opportunity Analyser
 including a citation suggestion of the tool.
            """
        )
    st.image("static/disclaimer.png")
    st.image("static/disclaimer_2.png")


def config_number_columns(df: pd.DataFrame, **kwargs) -> {}:
    """Create number column config info for st.dataframe() or st.data_editor."""
    column_config_all = {}
    for c in df.columns:
        column_config_all[c] = st.column_config.NumberColumn(
            **kwargs,
        )

    return column_config_all
