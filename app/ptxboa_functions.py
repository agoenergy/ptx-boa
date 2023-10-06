# -*- coding: utf-8 -*-
"""Utility functions for streamlit app."""
from urllib.parse import urlparse

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from PIL import Image


def calculate_results_single(api, settings):
    """Calculate results for single country pair."""
    res = api.calculate(
        scenario=settings["sel_scenario"],
        secproc_co2=settings["sel_secproc_co2"],
        secproc_water=settings["sel_secproc_water"],
        chain=settings["sel_chain"],
        res_gen=settings["sel_res_gen_name"],
        region=settings["sel_region"],
        country=settings["sel_country_name"],
        transport=settings["sel_transport"],
        ship_own_fuel=settings["sel_ship_own_fuel"],
        output_unit=settings["selOutputUnit"],
    )

    return res


def calculate_results(api, settings):
    # calculate results for all source regions:
    results_list = []
    for region in settings["region_list"]:
        settings2 = settings.copy()
        settings2["sel_region"] = region
        result_single = pd.DataFrame.from_dict(
            calculate_results_single(api, settings2)
        ).reset_index(drop=True)
        results_list.append(result_single)

    results = pd.concat(results_list, ignore_index=True)[
        ["source", "variable", "process_class", "value"]
    ]

    # aggregate costs (without LC):
    res_costs = results.loc[results["variable"] != "LC"].pivot_table(
        index="source", columns="process_class", values="value", aggfunc=sum
    )

    # Calculate total costs:
    res_costs["Total"] = res_costs.sum(axis=1)

    # replace region codes with region names:
    index_mapping = api.get_dimension("region").set_index("region_code")["region_name"]
    res_costs.index = res_costs.index.map(index_mapping)
    return res_costs


# Settings:
def create_sidebar(api):
    st.sidebar.subheader("Main settings:")
    settings = {}
    settings["sel_region"] = st.sidebar.selectbox(
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
    settings["sel_country_name"] = st.sidebar.selectbox(
        "Demand country:",
        api.get_dimension("country").index,
        help=(
            "The country you aim to export to. Some key info on the demand country you "
            "choose here are displayed in the info box."
        ),
    )
    settings["sel_chain"] = st.sidebar.selectbox(
        "Product (electrolyzer type):",
        api.get_dimension("chain").index,
        help=(
            "The product you want to export including the electrolyzer technology "
            "to use."
        ),
    )
    settings["sel_res_gen_name"] = st.sidebar.selectbox(
        "Renewable electricity source (for selected supply region):",
        api.get_dimension("res_gen").index,
        help=(
            "The source of electricity for the selected source country. For all "
            "other countries Wind-PV hybrid systems will be used (an optimized mixture "
            "of PV and wind onshore plants)"
        ),
    )
    settings["sel_scenario"] = st.sidebar.selectbox(
        "Data year (cost reduction pathway):",
        api.get_dimension("scenario").index,
        help=(
            "To cover parameter uncertainty and development over time, we provide "
            "cost reduction pathways (high / medium / low) for 2030 and 2040."
        ),
    )

    st.sidebar.subheader("Additional settings:")
    settings["sel_secproc_co2"] = st.sidebar.radio(
        "Carbon source:",
        api.get_dimension("secproc_co2").index,
        horizontal=True,
        help="Help text",
    )
    settings["sel_secproc_water"] = st.sidebar.radio(
        "Water source:",
        api.get_dimension("secproc_water").index,
        horizontal=True,
        help="Help text",
    )
    settings["sel_transport"] = st.sidebar.radio(
        "Mode of transportation (for selected supply country):",
        api.get_dimension("transport").index,
        horizontal=True,
        help="Help text",
    )
    if settings["sel_transport"] == "Ship":
        settings["sel_ship_own_fuel"] = st.sidebar.toggle(
            "For shipping option: Use the product as own fuel?",
            help="Help text",
        )
    settings["selOutputUnit"] = st.sidebar.radio(
        "Unit for delivered costs:",
        api.get_dimension("output_unit").index,
        horizontal=True,
        help="Help text",
    )

    st.sidebar.subheader("Dev:")
    region = api.get_dimension("region")
    settings["num_regions"] = st.sidebar.slider(
        "number of regions to calculate:",
        1,
        len(region[region["subregion_code"].isna()]),
        value=5,
    )
    return settings


def create_world_map(settings: dict, res_costs: pd.DataFrame):
    parameter_to_show_on_map = st.selectbox(
        "Select cost component:", res_costs.columns, index=len(res_costs.columns) - 1
    )
    title_string = (
        f"{parameter_to_show_on_map} cost of exporting {settings['sel_chain']} to "
        f"{settings['sel_country_name']}"
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

    fig.update_layout(coloraxis_colorbar={"title": settings["selOutputUnit"]})

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
    highlighted_row_index = settings["sel_region"]

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
        yaxis={"title": settings["selOutputUnit"]},
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)


def create_scatter_plot(df_res, settings: dict):
    df_res["Country"] = "Other countries"
    df_res.at[settings["sel_region"], "Country"] = settings["sel_region"]

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


def content_context_data(api):
    st.subheader(
        "What regulations and/or standards are relevant "
        "for which PTX BOA demand countries?"
    )
    data_countries = api.load_context_data("context_cs_countries")
    st.dataframe(data_countries, use_container_width=True)
    st.subheader("Are the following criteria considered in this scheme?")
    data_scope = api.load_context_data("context_cs_scope")
    st.dataframe(data_scope, use_container_width=True)


def content_dashboard(api, res_costs: dict, settings: pd.DataFrame):
    st.markdown("Welcome to our dashboard!")
    st.markdown(
        "Here you will find your central selection options, "
        "a first look at your results and links to more detailed result sheets."
    )
    st.divider()

    c_1, c_2 = st.columns([1, 2])
    with c_1:
        create_infobox(api, settings)

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


def content_market_scanning(res_costs: dict, settings: pd.DataFrame):
    st.markdown(
        "Get an overview of competing PTX BOA supply countries"
        "and potential demand countries"
    )
    st.markdown(
        "This sheet will help you to better evaluate your country's competitive "
        "position as well as your options on the emerging global H2 market. "
        "\n"
        "\n"
        "The left diagram shows you how your country ranks compared to other supply"
        "countries that target the same demand country market."
        "\n"
        "The diagrams on the right show transport distances between your country "
        "and potential PTX BOA demand countries "
        "as well as their projected H2 demands"
    )


def create_infobox(api, settings: dict):
    data = api.load_context_data("_context_data_infobox")
    st.markdown(f"**Key information on {settings['sel_country_name']}:**")
    demand = data.at[settings["sel_country_name"], "Projected H2 demand [2030]"]
    info1 = data.at[settings["sel_country_name"], "key_info_1"]
    info2 = data.at[settings["sel_country_name"], "key_info_2"]
    info3 = data.at[settings["sel_country_name"], "key_info_3"]
    info4 = data.at[settings["sel_country_name"], "key_info_4"]
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
    st.image(Image.open("static/sustainability.png"))
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
