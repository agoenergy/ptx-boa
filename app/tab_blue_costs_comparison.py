"""
Tab in the blue app which compares blue PtX vs. green PtX costs.

The blue PtX costs are calculated from the current settings.
The green PtX costs are an median, 25th, and 75th percentiles for costs of
all export countries and chains that have the current product as output product.
"""

import itertools
import logging
from typing import Literal

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app.ptxboa_functions import (
    calculate_cached,
    calculate_results_list_blue,
    read_markdown_file,
)
from ptxboa.api import PtxboaAPI
from ptxboa.static import OutputUnitType, ScenarioType, TargetCountryNameType

GREEN_COLOR = "#2fac66"
BLUE_COLOR = "#1E83B3"

COLUMN_NAME_MAP = {
    "product_type": "Primary energy type",
    "scenario": "Scenario",
    "country": "Import country",
    "transport": "Transport",
    "ship_own_fuel": "Ship use product as own fuel",
    "secproc_water": "Secondary water source",
    "secproc_co2": "Secondary CO₂ source",
    "res_gen": "Renewable energy source",
    "region": "Export country",
    "chain": "Conversion route",
}


@st.cache_data(show_spinner=False)
def get_no_green_ptx_import_countries(_api: PtxboaAPI):
    blue_countries = set(
        _api.get_dimension(dim="country", tool_version_color="blue").index
    )
    green_countries = set(
        _api.get_dimension(dim="country", tool_version_color="green").index
    )
    return blue_countries - green_countries


def product_dict(**kwargs):
    """Yield the cartesian product of a dictionary of lists.

    https://stackoverflow.com/a/5228294

    >>> list(product_dict(sting=["a", "b", "c"], number=[1, 2]))

    [{'sting': 'a', 'number': 1},
    {'sting': 'a', 'number': 2},
    {'sting': 'b', 'number': 1},
    {'sting': 'b', 'number': 2},
    {'sting': 'c', 'number': 1},
    {'sting': 'c', 'number': 2}]
    """
    keys = kwargs.keys()
    for instance in itertools.product(*kwargs.values()):
        yield dict(zip(keys, instance))


@st.cache_data(show_spinner=False)
def get_green_results(
    _api: PtxboaAPI,
    scenarios: list[ScenarioType],
    import_country: TargetCountryNameType,
    output_product: str,
    output_unit: OutputUnitType,
    green_param_set: Literal["restricted", "complete"] = "restricted",
):

    if output_product not in [
        "NH3-L",
        "B-DRI-S",
        "CHX-L",
        "H2-G",
        "CH3OH-L",
    ]:
        raise ValueError(f"invalid {output_product=}")

    green_blue_product_map = {"B-DRI-S": "DRI-S"}
    green_output_product = green_blue_product_map.get(output_product, output_product)

    if green_param_set == "complete":
        # complete parame set is too slow without caching.
        dimensions = {
            "transport": _api.get_dimension(
                "transport", tool_version_color="green"
            ).index.tolist(),
            "ship_own_fuel": [True, False],
            "secproc_water": _api.get_dimension(
                "secproc_water", tool_version_color="green"
            ).index.tolist(),
            "secproc_co2": _api.get_dimension(
                "secproc_co2", tool_version_color="green"
            ).index.tolist(),
            "res_gen": _api.get_dimension(
                "res_gen", tool_version_color="green"
            ).index.tolist(),
            "region": (
                _api.get_dimension("region", tool_version_color="green")
                .loc[
                    _api.get_dimension("region", tool_version_color="green")[
                        "subregion_code"
                    ]
                    == ""
                ]
                .index.to_list()
            ),
            "chain": (
                _api.get_dimension("chain", tool_version_color="green")
                .loc[
                    _api.get_dimension("chain", tool_version_color="green")["flow_out"]
                    == green_output_product
                ]
                .index.tolist()
            ),
        }

    elif green_param_set == "restricted":
        dimensions = {
            "transport": ["Pipeline"],
            "ship_own_fuel": [False],
            "secproc_water": ["Specific costs"],
            "secproc_co2": ["Specific costs"],
            "res_gen": ["Wind-PV-Hybrid"],
            "region": (
                _api.get_dimension("region", tool_version_color="green")
                .loc[
                    _api.get_dimension("region", tool_version_color="green")[
                        "subregion_code"
                    ]
                    == ""
                ]
                .index.to_list()
            ),
            "chain": (
                _api.get_dimension("chain", tool_version_color="green")
                .loc[
                    _api.get_dimension("chain", tool_version_color="green")["flow_out"]
                    == green_output_product
                ]
                .index.tolist()
            ),
        }
    else:
        raise ValueError(f"Unknown {green_param_set=}")

    raw = []

    for scenario in scenarios:
        for param_set in list(product_dict(**dimensions)):
            try:
                complete_param_set = param_set | {
                    "scenario": scenario,
                    "country": import_country,
                }
                costs = calculate_cached(
                    _api,
                    user_data=None,  # we do not respect user data here
                    optimize_flh=False,  # TODO revert to True when ready
                    use_user_data_for_optimize_flh=False,
                    output_unit=output_unit,
                    tool_version_color="green",
                    **complete_param_set,
                ).costs

                value = costs["values"].sum()
                # get parameters from result df
                result_record = costs.iloc[0].to_dict()
                # update input parameters with result parameters
                # they differ e.g. when pipeline transport was not possible
                result_record = {
                    k: result_record.get(k, v) for k, v in complete_param_set.items()
                }
                # add value to result record
                result_record["values"] = value
                raw.append(result_record)
            except Exception as exc:
                logging.info(f"could not get data: {exc}")

    df = pd.DataFrame.from_records(raw)
    df.insert(0, "product_type", "Renewable based")
    # reorder columns
    df = df[["values"] + [c for c in df.columns if c != "values"]]
    return df


def get_blue_results(api, scenarios):
    df = calculate_results_list_blue(
        api,
        parameter_to_change="scenario",
        parameter_list=scenarios,
        apply_user_data=True,
        override_session_state=None,
        agg_costs=False,
    )[0]
    df = df.drop(columns=["process_type", "process_subtype", "cost_type"])
    # add ship_own_fuel as it is not returned from api.calculate
    df["ship_own_fuel"] = st.session_state["ship_own_fuel"]
    group_by_cols = [c for c in df.columns if c != "values"]
    df = df.groupby(by=group_by_cols, dropna=False).sum()
    df = df.reset_index()
    df.insert(0, "product_type", "Natural gas based")
    df = df[["values"] + [c for c in df.columns if c != "values"]]
    return df


def get_data(
    api, scenarios: list[ScenarioType], import_country, output_product, output_unit
):
    with st.spinner("Calculating green results"):
        costs_green_raw = get_green_results(
            api,
            scenarios=scenarios,
            import_country=import_country,
            output_product=output_product,
            output_unit=output_unit,
        )

    costs_blue_raw = get_blue_results(api, scenarios)

    return relabel_chains(api, costs_blue_raw), costs_green_raw


def relabel_chains(api, df):
    chain_labels = api.get_dimension("chain")["chain_name"].to_dict()
    df["chain"] = df["chain"].replace(chain_labels)
    return df


def rename_data_columns(df):
    df = df.rename(columns=COLUMN_NAME_MAP)
    return df


def crude_steel_warning():
    st.warning(
        read_markdown_file(
            "md/tab_blue_cost_comparison/crude_steel_comparison_warning.md"
        )
    )


def content_costs_comparison(api):
    with st.popover("*Help*", width="stretch"):
        st.markdown(
            read_markdown_file(
                "md/tab_blue_cost_comparison/whatisthis_cost_comparison.md"
            )
        )

    with st.container(border=True):
        # --------------------------
        # Parameter checks
        # --------------------------
        is_invalid = False
        if st.session_state["country"] in get_no_green_ptx_import_countries(api):
            is_invalid = True
            st.warning(
                f"Renewable based cost data not available for "
                f"{st.session_state['country']}. No comparison possible."
            )
        if st.session_state["output_product"] == "STL-S":
            is_invalid = True
            crude_steel_warning()
        if is_invalid:
            return

        costs_blue_raw, costs_green_raw = get_data(
            api,
            scenarios=["2030 (medium)", "2040 (medium)"],
            import_country=st.session_state["country"],
            output_product=st.session_state["output_product"],
            output_unit=st.session_state["output_unit"],
        )
        title_string = (
            f"Cost of importing "
            f"{st.session_state['output_product_label']} to "
            f"{st.session_state['country']}"
        )
        st.subheader(title_string)

        # --------------------------
        # Display samples
        # --------------------------
        st.divider()
        st.markdown("##### Option 1: Boxplot")
        fig = create_figure(costs_blue_raw, costs_green_raw, green_display="box")
        st.plotly_chart(fig)
        st.divider()

        st.markdown("##### Option 2: Violin")
        fig = create_figure(costs_blue_raw, costs_green_raw, green_display="violin")
        st.plotly_chart(fig)
        st.divider()

        st.markdown("##### Option 3: Rectangle")
        fig = create_figure(costs_blue_raw, costs_green_raw, green_display="bar")
        st.plotly_chart(fig)
        # --------------------------

        with st.expander("**Data**"):
            data = pd.concat([costs_blue_raw, costs_green_raw])
            st.dataframe(
                rename_data_columns(data),
                hide_index=True,
                column_config={
                    "values": st.column_config.NumberColumn(
                        label="Total cost",
                        format=f"%.1f {st.session_state['output_unit']}",
                    ),
                    "Ship use product as own fuel": st.column_config.TextColumn(),
                },
            )


def create_figure(
    costs_blue_raw: pd.DataFrame,
    costs_green_raw: pd.DataFrame,
    green_display: Literal["box", "violin", "bar"],
):
    fig = go.Figure()
    HOVER_CUSTOM_DATA_COLS = {
        k: COLUMN_NAME_MAP[k]
        for k in [
            "product_type",
            "scenario",
            "country",
            "transport",
            "ship_own_fuel",
            "secproc_water",
            "secproc_co2",
            "res_gen",
            "region",
            "chain",
        ]
    }
    HOVERTEMPLATE = (
        "<b>Total cost: %{y:.1f} "
        + st.session_state["output_unit"]
        + "</b><br><br>"
        + "<br>".join(
            [
                f"{label}: %{{customdata[{i}]}}"
                for i, label in enumerate(HOVER_CUSTOM_DATA_COLS.values())
            ]
        )
        + "<extra></extra>"
    )
    GREEN_NAME = (
        f"Renewable based {st.session_state['output_product_label']} cost range"
    )

    # =====================================================================
    # OPTIONS
    # ---------------------------------------------------------------------
    # A) BOX
    # ---------------------------------------------------------------------
    if green_display == "box":
        fig.add_trace(
            go.Box(
                x=costs_green_raw["scenario"],
                y=costs_green_raw["values"],
                name=GREEN_NAME,
                marker_color=GREEN_COLOR,
                marker_size=3,
                customdata=costs_green_raw[list(HOVER_CUSTOM_DATA_COLS.keys())],
                hovertemplate=HOVERTEMPLATE,
                boxpoints="all",
                hoveron="points",
            )
        )

    # ---------------------------------------------------------------------
    # B) VIOLIN
    # ---------------------------------------------------------------------
    if green_display == "violin":
        fig.add_trace(
            go.Violin(
                x=costs_green_raw["scenario"],
                y=costs_green_raw["values"],
                name=GREEN_NAME,
                marker_color=GREEN_COLOR,
                marker_size=3,
                customdata=costs_green_raw[list(HOVER_CUSTOM_DATA_COLS.keys())],
                hovertemplate=HOVERTEMPLATE,
                points="all",
                hoveron="points",
                spanmode="hard",
            )
        )

    # ---------------------------------------------------------------------
    # C) Stripe + Bar
    # ---------------------------------------------------------------------
    if green_display == "bar":
        fig.add_trace(
            go.Box(
                x=costs_green_raw["scenario"],
                y=costs_green_raw["values"],
                boxpoints="all",
                customdata=costs_green_raw[list(HOVER_CUSTOM_DATA_COLS.keys())],
                hovertemplate=HOVERTEMPLATE,
                hoveron="points",
                jitter=0.2,
                pointpos=-0.5,
                fillcolor="rgba(255,255,255,0)",
                line={
                    "color": "rgba(255,255,255,0)",
                },
                marker={
                    "color": GREEN_COLOR,
                    "size": 3,
                },
                alignmentgroup=True,
                showlegend=False,
                legendgroup="green",
            )
        )

        scenario_min_max = costs_green_raw.groupby("scenario")["values"].agg(
            ["min", "max"]
        )

        fig.add_trace(
            go.Bar(
                x=scenario_min_max.index,
                y=scenario_min_max["max"] - scenario_min_max["min"],
                base=scenario_min_max["min"],
                marker={
                    "color": GREEN_COLOR,
                    "opacity": 0.5,
                },
                name=GREEN_NAME,
                legendgroup="green",
            )
        )

    # =====================================================================
    fig.add_trace(
        go.Scatter(
            x=costs_blue_raw["scenario"],
            y=costs_blue_raw["values"],
            name=f"Natural gas based {st.session_state['output_product_label']}",
            marker_color=BLUE_COLOR,
            mode="markers",
            marker={
                "size": 15,
                "symbol": "circle-dot",
                "line": {
                    "width": 2,
                    "color": "DarkSlateGrey",
                },
            },
            customdata=costs_blue_raw[list(HOVER_CUSTOM_DATA_COLS.keys())],
            hovertemplate=HOVERTEMPLATE,
        )
    )
    fig.update_layout(
        xaxis={
            "title": {"text": "Scenario"},
            "tickformat": ",",
        },
        yaxis={
            "title": {"text": st.session_state["output_unit"]},
            "range": [0, None],
            "tickformat": ",",
            "rangemode": "tozero",
        },
        boxmode="group",
        separators=". ",
    )

    return fig
