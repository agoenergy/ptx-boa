# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from ptxboa.api import PtxboaAPI


def calculate_results_single(api: PtxboaAPI, settings):
    """Calculate results for single country pair."""
    res = api.calculate(**settings)

    return res


def calculate_results(
    api: PtxboaAPI, settings: dict, region_list: list = None
) -> pd.DataFrame:
    """Calculate results for source regions and one selected target country.

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
        res_single = api.calculate(**settings2)
        res_list.append(res_single)
    res = pd.concat(res_list)
    return res


def aggregate_costs(res_details: pd.DataFrame) -> pd.DataFrame:
    """Aggregate detailed costs."""
    # Exclude levelized costs:
    res = res_details.loc[res_details["cost_type"] != "LC"]
    res = res.pivot_table(
        index="region", columns="process_type", values="values", aggfunc="sum"
    )
    # calculate total costs:
    res["Total"] = res.sum(axis=1)

    # TODO exclude countries with total costs of 0 - maybe remove later:
    res = res.loc[res["Total"] != 0]
    return res


# Settings:
def create_sidebar(api: PtxboaAPI):
    st.sidebar.subheader("Main settings:")
    settings = {}
    settings["region"] = st.sidebar.selectbox(
        "Supply country / region:",
        # TODO: replace with complete list of regions once calculation time is reduced:
        ("Argentina", "Morocco", "South Africa"),
        help=(
            "One supply country or region can be selected here, and detailed settings "
            "can be selected for this region below "
            "(RE source, mode of transportation). For other regions, "
            "default settings will be used."
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

    return settings


def create_world_map(settings: dict, res_costs: pd.DataFrame):
    parameter_to_show_on_map = st.selectbox(
        "Select cost component:", res_costs.columns, index=len(res_costs.columns) - 1
    )
    title_string = (
        f"{parameter_to_show_on_map} cost of exporting {settings['chain']} to "
        f"{settings['country']}"
    )
    # Create a choropleth world map using Plotly Express
    fig = px.choropleth(
        locations=res_costs.index,  # List of country codes or names
        locationmode="country names",  # Use country names as locations
        color=res_costs[parameter_to_show_on_map],  # Color values for the countries
        hover_name=res_costs.index,  # Names to display on hover
        color_continuous_scale="Turbo",  # Choose a color scale
        title=title_string,
    )

    # Add black borders to the map
    fig.update_geos(
        showcountries=True,  # Show country borders
        showcoastlines=False,  # Hide coastlines for a cleaner look
        bgcolor="lightgray",  # Set background color
        countrycolor="white",  # Set default border color for other countries
        showland=True,
        landcolor="white",  # Set land color
        oceancolor="lightblue",  # Set ocean color
    )

    fig.update_layout(coloraxis_colorbar={"title": settings["output_unit"]})

    # Display the map using st.plotly_chart
    st.plotly_chart(fig, use_container_width=True)
    return


def create_bar_chart_costs(res_costs: pd.DataFrame):
    fig = px.bar(res_costs, x=res_costs.index, y=res_costs.columns[:-1], height=500)

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

    fig.update_layout(
        title="Total cost by region",
        yaxis_title="USD/kWh",
    )
    st.plotly_chart(fig, use_container_width=True)


def create_box_plot(res_costs: pd.DataFrame, settings: dict):
    # Create a subplot with one row and one column
    fig = go.Figure()

    # Specify the row index of the data point you want to highlight
    highlighted_row_index = settings["region"]

    # Extract the value from the specified row and column
    highlighted_value = res_costs.at[highlighted_row_index, "Total"]

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
    st.markdown("Welcome to our dashboard!")
    st.markdown(
        "Here you will find your central selection options, "
        "a first look at your results and links to more detailed result sheets."
    )
    st.divider()

    c_1, c_2 = st.columns([1, 2])
    with c_1:
        create_infobox(context_data, settings)

    with c_2:
        create_world_map(settings, res_costs)

    st.divider()

    c_3, c_4 = st.columns(2)

    with c_3:
        create_box_plot(res_costs, settings)
    with c_4:
        filtered_data = res_costs[res_costs.index == "Argentina"]
        create_bar_chart_costs(filtered_data)

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
    st.markdown("**Market Scanning**")
    st.markdown(
        """This is the markt scanning sheet. It will contain scatter plots
        that allows users to compare regions by total cost, transportation
        distance and H2 demand."""
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
    st.dataframe(df_plot, use_container_width=True)


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
        .loc[api.get_dimension("region")["subregion_code"].isna()]
        .index.to_list()
    )

    # ensure that target country is not in list of regions:
    if settings["country"] in region_list_without_subregions:
        region_list_without_subregions.remove(settings["country"])

    df = df.loc[region_list_without_subregions]

    return df


def content_costs_by_region(
    api: PtxboaAPI, res_costs: pd.DataFrame, settings: dict
) -> None:
    """Create content for the "costs by region" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    res_costs : pd.DataFrame
        Results.
    """
    st.markdown("**Costs by region**")
    st.markdown(
        """On this sheet, users can analyze total cost and cost components for
          different supply countries. Data is represented as a bar chart and
            in tabular form. \n\n Data can be filterend and sorted."""
    )
    c1, c2 = st.columns([1, 5])
    with c1:
        # filter data:
        df_res = res_costs.copy()
        # remove subregions:
        df_res = remove_subregions(api, df_res, settings)

        # select filter:
        show_which_data = st.radio(
            "Select regions to display:",
            ["All", "Ten cheapest", "Manual select"],
            index=0,
        )

        # apply filter:
        if show_which_data == "Ten cheapest":
            df_res = df_res.nsmallest(10, "Total")
        elif show_which_data == "Manual select":
            ind_select = st.multiselect(
                "Select regions:",
                df_res.index.values,
                default=[settings["region"]],
            )
            df_res = df_res.loc[ind_select]

        # sort:
        sort_ascending = st.toggle("Sort by total costs?", value=True)
        if sort_ascending:
            df_res = df_res.sort_values(["Total"], ascending=True)
    with c2:
        # create graph:
        create_bar_chart_costs(df_res)

    st.write("**Data:**")
    st.dataframe(df_res, use_container_width=True)


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
    st.markdown("**Deep-dive countries.**")

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

    list_data_types = ["full load hours", "total costs"]
    data_selection = st.radio(
        "Select data type",
        list_data_types,
        horizontal=True,
        key="sel_data_ddc",
    )
    if data_selection == "full load hours":
        ind_1 = input_data["source_region_code"].isin(region_list)
        ind_2 = input_data["parameter_code"] == "full load hours"
        ind_3 = input_data["process_code"].isin(
            [
                "Wind Onshore",
                "Wind Offshore",
                "PV tilted",
                "Wind-PV-Hybrid",
            ]
        )
        x = "process_code"
        y = "value"

        df = input_data.loc[ind_1 & ind_2 & ind_3]
    if data_selection == "total costs":
        df = res_costs.copy()
        df = res_costs.loc[region_list].rename({"Total": data_selection}, axis=1)
        df = df.rename_axis("source_region_code", axis=0)
        x = None
        y = data_selection
        st.markdown("TODO: fix surplus countries in data table")

    # create plot:
    create_box_plot_with_data(df, x=x, y=y)


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
    st.markdown("**Input data**")

    # get input data:
    input_data = api.get_input_data(settings["scenario"])

    # filter data:
    region_list_without_subregions = (
        api.get_dimension("region")
        .loc[api.get_dimension("region")["subregion_code"].isna()]
        .index.to_list()
    )
    input_data = input_data.loc[
        input_data["source_region_code"].isin(region_list_without_subregions)
    ]
    list_data_types = ["CAPEX", "full load hours", "WACC"]
    data_selection = st.radio("Select data type", list_data_types, horizontal=True)
    if data_selection == "CAPEX":
        parameter_code = ["CAPEX"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        ind1 = input_data["parameter_code"].isin(parameter_code)
        ind2 = input_data["process_code"].isin(process_code)
        df = input_data.loc[ind1 & ind2]
        x = "process_code"
    if data_selection == "full load hours":
        parameter_code = ["full load hours"]
        process_code = [
            "Wind Onshore",
            "Wind Offshore",
            "PV tilted",
            "Wind-PV-Hybrid",
        ]
        ind1 = input_data["parameter_code"].isin(parameter_code)
        ind2 = input_data["process_code"].isin(process_code)
        df = input_data.loc[ind1 & ind2]
        x = "process_code"
    if data_selection == "WACC":
        parameter_code = ["interest rate"]
        ind1 = input_data["parameter_code"].isin(parameter_code)
        df = input_data.loc[ind1]
        x = "parameter_code"

    # create plot:
    create_box_plot_with_data(df, x)


def create_box_plot_with_data(df, x, y="value"):
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.markdown("**Figure:**")
        fig = px.box(df, x=x, y=y)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        # show data as table:
        df_tab = df.pivot_table(
            index="source_region_code", columns=x, values=y, aggfunc="sum"
        )
        st.markdown("**Data:**")
        st.dataframe(df_tab, use_container_width=True)


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
    """Display information on a chosen demand country."""
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
    st.markdown(
        """This page contains detailed information
         and a collection of links for further reading."""
    )
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
    st.markdown("**Hydrogen strategy documents:**")
    st.markdown(data["h2_strategy_documents"])

    st.markdown("**Hydrogen strategy authorities:**")
    st.markdown(data["h2_strategy_authorities"])

    st.markdown("**Information on certification schemes:**")
    st.markdown(data["certification_info"])
    st.markdown(f"*Source: {data['source_certification_info']}*")

    st.markdown("**H2 trade characteristics:**")
    st.markdown(data["h2_trade_characteristics"])
    st.markdown(f"*Source: {data['source_h2_trade_characteristics']}*")

    st.markdown("**LNG import terminals:**")
    st.markdown(data["lng_import_terminals"])
    st.markdown(f"*Source: {data['source_lng_import_terminals']}*")

    st.markdown("**H2 pipeline projects:**")
    st.markdown(data["h2_pipeline_projects"])
    st.markdown(f"*Source: {data['source_h2_pipeline_projects']}*")


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
    """Display information on a chosen certification scheme."""
    df = context_data["certification_schemes"]
    helptext = "Select the certification scheme you want to know more about."
    scheme_id = st.selectbox("Select scheme:", df["ID"], help=helptext)
    data = df.loc[df["ID"] == scheme_id].iloc[0].to_dict()

    st.header(data["name"])

    st.markdown(data["description"])

    st.subheader("Characteristics")

    st.markdown(
        f"- **Relation to other standards:** {data['relation_to_other_standards']}"
    )
    st.markdown(f"- **Geographic scope:** {data['geographic_scope']}")
    st.markdown(f"- **PTXBOA demand countries:** {data['ptxboa_demand_countries']}")
    st.markdown(f"- **Labels:** {data['label']}")
    st.markdown(f"- **Lifecycle scope:** {data['lifecycle_scope']}")

    st.subheader("Scope")
    st.markdown("- **Emissions:**")
    st.markdown(data["scope_emissions"])

    st.markdown("- **Electricity:**")
    st.markdown(data["scope_electricity"])

    st.markdown("- **Water:**")
    st.markdown(data["scope_water"])

    st.markdown("- **Biodiversity:**")
    st.markdown(data["scope_biodiversity"])

    st.markdown("- **Other:**")
    st.markdown(data["scope_other"])

    st.subheader("Sources")
    st.markdown(data["sources"])


def create_content_sustainability(context_data: dict):
    """Display information on sustainability issues."""
    df = context_data["sustainability"]
    st.image("static/sustainability.png")
    captiontext = (
        "Source: https://ptx-hub.org/wp-content/uploads/2022/05/"
        "PtX-Hub-PtX.Sustainability-Dimensions-and-Concerns-Scoping-Paper.pdf"
    )
    st.caption(captiontext)

    c1, c2 = st.columns(2)
    with c1:
        helptext = "helptext"
        dimension = st.selectbox(
            "Select dimension:", df["dimension"].unique(), help=helptext
        )
    with c2:
        helptext = "helptext"
        question_type = st.radio(
            "Guardrails or goals?",
            ["Guardrails", "Goals"],
            help=helptext,
            horizontal=True,
        )
        data = df.loc[(df["dimension"] == dimension) & (df["type"] == question_type)]

    for topic in data["topic"].unique():
        st.markdown(f"**{topic}:**")
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
    """Display list of references."""
    df = context_data["literature"]
    markdown_text = ""
    for _ind, row in df.iterrows():
        if is_valid_url(row["url"]):
            text = (
                f"- **{row['short_name']}**: {row['long_name']} [Link]({row['url']})\n"
            )
        else:
            text = f"- **{row['short_name']}**: {row['long_name']}\n"
        markdown_text = markdown_text + text

    st.markdown(markdown_text)
