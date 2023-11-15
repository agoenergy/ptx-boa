# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from ptxboa.api import PtxboaAPI


@st.cache_data()
def calculate_results_single(
    _api: PtxboaAPI,
    settings: dict,
    user_data: pd.DataFrame | None = None,
) -> pd.DataFrame:
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
    res = _api.calculate(user_data=user_data, **settings)

    return res


def calculate_results_list(
    api: PtxboaAPI,
    parameter_to_change: str,
    parameter_list: list = None,
    user_data: pd.DataFrame | None = None,
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

    # copy settings from session_state:
    settings = {}
    for key in [
        "chain",
        "country",
        "output_unit",
        "region",
        "res_gen",
        "scenario",
        "secproc_co2",
        "secproc_water",
        "ship_own_fuel",
        "transport",
    ]:
        settings[key] = st.session_state[key]

    for parameter in parameter_list:
        settings2 = settings.copy()
        settings2[parameter_to_change] = parameter
        res_single = calculate_results_single(api, settings2, user_data=user_data)
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
        height=600,  # height of figure
        margin={"t": 20, "b": 20, "l": 20, "r": 20},  # reduce margin around figure
    )

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


def content_dashboard(api, res_costs: dict, context_data: dict):
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

    with c_1:
        create_world_map(api, res_costs)

    with c_2:
        # create box plot and bar plot:
        fig1 = create_box_plot(res_costs)
        filtered_data = res_costs[res_costs.index == st.session_state["region"]]
        fig2 = create_bar_chart_costs(filtered_data)
        doublefig = make_subplots(rows=1, cols=2, shared_yaxes=True)

        for trace in fig1.data:
            trace.showlegend = False
            doublefig.add_trace(trace, row=1, col=1)
        for trace in fig2.data:
            doublefig.add_trace(trace, row=1, col=2)

        doublefig.update_layout(barmode="stack")
        doublefig.update_layout(title_text="Cost distribution and details:")
        st.plotly_chart(doublefig, use_container_width=True)

        create_infobox(context_data)


def content_market_scanning(api: PtxboaAPI, res_costs: pd.DataFrame) -> None:
    """Create content for the "market scanning" sheet.

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
**Market scanning: Get an overview of competing PTX BOA supply countries
 and potential demand countries.**

This sheet helps you to better evaluate your country's competitive position
 as well as your options on the emerging global H2 market.

            """
        )

    # get input data:
    input_data = api.get_input_data(st.session_state["scenario"])

    # filter shipping and pipeline distances:
    distances = input_data.loc[
        (input_data["parameter_code"].isin(["shipping distance", "pipeline distance"]))
        & (input_data["target_country_code"] == st.session_state["country"]),
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
    df_plot = remove_subregions(api, df_plot, st.session_state["country"])

    # create plot:st.session_state
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


def remove_subregions(api: PtxboaAPI, df: pd.DataFrame, country_name: str):
    """Remove subregions from a dataframe.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

    df : pd.DataFrame
        pandas DataFrame with list of regions as index.

    country_name : str
        name of target country. Is removed from region list if it is also in there.

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
    if country_name in region_list_without_subregions:
        region_list_without_subregions.remove(country_name)

    df = df.loc[region_list_without_subregions]

    return df


def content_compare_costs(api: PtxboaAPI, res_costs: pd.DataFrame) -> None:
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

    def display_costs(df_costs: pd.DataFrame, key: str, titlestring: str):
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
            fig = create_bar_chart_costs(
                df_res,
                current_selection=st.session_state[key],
            )
            st.plotly_chart(fig, use_container_width=True)

        with st.expander("**Data**"):
            column_config = config_number_columns(
                df_res, format=f"%.1f {st.session_state['output_unit']}"
            )
            st.dataframe(df_res, use_container_width=True, column_config=column_config)

    res_costs_without_subregions = remove_subregions(
        api, res_costs, st.session_state["country"]
    )
    display_costs(res_costs_without_subregions, "region", "Costs by region:")

    # Display costs by scenario:
    res_scenario = calculate_results_list(
        api, "scenario", user_data=st.session_state["user_changes_df"]
    )
    display_costs(res_scenario, "scenario", "Costs by data scenario:")

    # Display costs by RE generation:
    # TODO: remove PV tracking manually, this needs to be fixed in data
    list_res_gen = api.get_dimension("res_gen").index.to_list()
    list_res_gen.remove("PV tracking")
    res_res_gen = calculate_results_list(
        api,
        "res_gen",
        parameter_list=list_res_gen,
        user_data=st.session_state["user_changes_df"],
    )
    display_costs(res_res_gen, "res_gen", "Costs by renewable electricity source:")

    # TODO: display costs by chain


def content_deep_dive_countries(api: PtxboaAPI, res_costs: pd.DataFrame) -> None:
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

    input_data = api.get_input_data(st.session_state["scenario"])

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
        missing_index_name = "parameter_code"
        missing_index_value = "full load hours"
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
            missing_index_name=missing_index_name,
            missing_index_value=missing_index_value,
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


def content_input_data(api: PtxboaAPI) -> None:
    """Create content for the "input data" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class

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

    st.subheader("Region specific data:")
    # get input data:
    input_data = api.get_input_data(
        st.session_state["scenario"],
        user_data=st.session_state["user_changes_df"],
    )

    # filter data:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"] == ""]
        .index.to_list()
    )
    input_data_without_subregions = input_data.loc[
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
        missing_index_name = "parameter_code"
        missing_index_value = "CAPEX"
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
        missing_index_name = "parameter_code"
        missing_index_value = "full load hours"
        column_config = {"format": "%.0f h/a", "min_value": 0, "max_value": 8760}

    if data_selection == "interest rate":
        parameter_code = ["interest rate"]
        process_code = [""]
        x = "parameter_code"
        column_config = {"format": "%.3f", "min_value": 0, "max_value": 1}
        missing_index_name = "parameter_code"
        missing_index_value = "interest rate"

    c1, c2 = st.columns(2, gap="medium")
    with c2:
        # show data:
        st.markdown("**Data:**")
        df = display_and_edit_data_table(
            input_data=input_data_without_subregions,
            missing_index_name=missing_index_name,
            missing_index_value=missing_index_value,
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

    st.divider()
    st.subheader("Data that is identical for all regions:")

    input_data_global = input_data.loc[input_data["source_region_code"] == ""]

    # filter processes:
    processes = api.get_dimension("process")

    list_processes_transport = processes.loc[
        processes["is_transport"], "process_name"
    ].to_list()

    list_processes_not_transport = processes.loc[
        ~processes["is_transport"], "process_name"
    ].to_list()
    st.markdown("**Conversion processes:**")
    df = display_and_edit_data_table(
        input_data_global,
        missing_index_name="source_region_code",
        missing_index_value=None,
        parameter_code=[
            "CAPEX",
            "OPEX (fix)",
            "lifetime / amortization period",
            "efficiency",
        ],
        process_code=list_processes_not_transport,
        index="process_code",
        columns="parameter_code",
    )
    st.markdown("**Transportation processes:**")
    st.markdown("TODO: fix data")
    df = display_and_edit_data_table(
        input_data_global,
        missing_index_name="source_region_code",
        missing_index_value=None,
        parameter_code=[
            "losses (own fuel, transport)",
            "levelized costs",
            "lifetime / amortization period",
            # FIXME: add bunker fuel consumption
        ],
        process_code=list_processes_transport,
        index="process_code",
        columns="parameter_code",
    )

    # If there are user changes, display them:
    display_user_changes()


def reset_user_changes():
    """Reset all user changes."""
    if st.session_state["user_changes_df"] is not None:
        st.session_state["user_changes_df"] = None


def display_user_changes():
    """Display input data changes made by user."""
    if st.session_state["user_changes_df"] is not None:
        st.subheader("Data modifications:")
        st.write("**Input data has been modified!**")
        st.dataframe(
            st.session_state["user_changes_df"].style.format(precision=3),
            hide_index=True,
        )


def display_and_edit_data_table(
    input_data: pd.DataFrame,
    missing_index_name: str,
    missing_index_value: str,
    source_region_code: list = None,
    parameter_code: list = None,
    process_code: list = None,
    index: str = "source_region_code",
    columns: str = "process_code",
    values: str = "value",
    column_config: dict = None,
    key_suffix: str = "",
) -> pd.DataFrame:
    """Display selected input data as 2D table, which can also be edited."""
    # filter data:
    df = input_data.copy()
    if source_region_code is not None:
        df = df.loc[df["source_region_code"].isin(source_region_code)]
    if parameter_code is not None:
        df = df.loc[df["parameter_code"].isin(parameter_code)]
    if process_code is not None:
        df = df.loc[df["process_code"].isin(process_code)]

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
            "missing_index_name": missing_index_name,
            "missing_index_value": missing_index_value,
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


def register_user_changes(
    missing_index_name: str,
    missing_index_value: str,
    index: str,
    columns: str,
    values: str,
    df_tab: pd.DataFrame,
    key: str,
):
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

    # add missing key (the info that is not contained in the 2D table):
    res[missing_index_name] = missing_index_value

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


def create_infobox(context_data: dict):
    data = context_data["infobox"]
    st.markdown(f"**Key information on {st.session_state['country']}:**")
    demand = data.at[st.session_state["country"], "Projected H2 demand [2030]"]
    info1 = data.at[st.session_state["country"], "key_info_1"]
    info2 = data.at[st.session_state["country"], "key_info_2"]
    info3 = data.at[st.session_state["country"], "key_info_3"]
    info4 = data.at[st.session_state["country"], "key_info_4"]
    st.markdown(f"* Projected H2 demand in 2030: {demand}")

    def write_info(info):
        if isinstance(info, str):
            st.markdown(f"* {info}")

    write_info(info1)
    write_info(info2)
    write_info(info3)
    write_info(info4)


def config_number_columns(df: pd.DataFrame, **kwargs) -> {}:
    """Create number column config info for st.dataframe() or st.data_editor."""
    column_config_all = {}
    for c in df.columns:
        column_config_all[c] = st.column_config.NumberColumn(
            **kwargs,
        )

    return column_config_all
