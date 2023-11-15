# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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


def config_number_columns(df: pd.DataFrame, **kwargs) -> {}:
    """Create number column config info for st.dataframe() or st.data_editor."""
    column_config_all = {}
    for c in df.columns:
        column_config_all[c] = st.column_config.NumberColumn(
            **kwargs,
        )

    return column_config_all
