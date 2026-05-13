"""
Tab in the blue app which compares blue PtX vs. green PtX costs.

The blue PtX costs are calculated from the current settings.
The green PtX costs are an median, 25th, and 75th percentiles for costs of
all export countries and chains that have the current product as output product.
"""

import itertools
import json
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
                    == output_product
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
                    == output_product
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
                costs = (
                    calculate_cached(
                        _api,
                        user_data=None,  # we do not respect user data here
                        optimize_flh=False,  # TODO revert to True when ready
                        use_user_data_for_optimize_flh=False,
                        scenario=scenario,
                        country=import_country,
                        output_unit=output_unit,
                        tool_version_color="green",
                        **param_set,
                    )
                    .costs["values"]
                    .sum()
                )

                raw.append(
                    {
                        "scenario": scenario,
                        "country": import_country,
                        "values": costs,
                        **param_set,
                    }
                )
            except Exception as exc:
                logging.info(f"could not get data: {exc}")

    df = pd.DataFrame.from_records(raw)
    df.insert(0, "product_type", "green")
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
    group_by_cols = [c for c in df.columns if c != "values"]
    df = df.groupby(by=group_by_cols, dropna=False).sum()
    df = df.reset_index()
    df.insert(0, "product_type", "blue")
    df = df[["values"] + [c for c in df.columns if c != "values"]]
    return df


def get_data(
    api, scenarios: list[ScenarioType], import_country, output_product, output_unit
):
    with st.spinner("Calculating green results"):
        cost_green_raw = get_green_results(
            api,
            scenarios=scenarios,
            import_country=import_country,
            output_product=output_product,
            output_unit=output_unit,
        )

    costs_blue_raw = get_blue_results(api, scenarios)

    return costs_blue_raw, cost_green_raw


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
        if st.session_state["output_product"] == "STL-S":
            crude_steel_warning()
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
        fig = go.Figure()
        fig.add_trace(
            go.Box(
                x=costs_green_raw["scenario"],
                y=costs_green_raw["values"],
                name=f"Green {st.session_state['output_product_label']} cost range",
                marker_color=GREEN_COLOR,
                customdata=get_hoverdata(costs_green_raw),
                hovertemplate="%{customdata}<extra></extra>",
                boxpoints="all",
            )
        )
        fig.add_trace(
            go.Scatter(
                x=costs_blue_raw["scenario"],
                y=costs_blue_raw["values"],
                name=f"Blue {st.session_state['output_product_label']}",
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
            },
            boxmode="group",
            separators=". ",
        )
        st.plotly_chart(fig)

        with st.expander("**Data**"):
            data = pd.concat([costs_blue_raw, costs_green_raw])
            st.dataframe(
                data,
                column_config={
                    "values": st.column_config.NumberColumn(
                        label="Total cost",
                        format=f"%.1f {st.session_state['output_unit']}",
                    )
                },
            )


def get_hoverdata(df):
    df = df.drop(columns=["product_type", "values"])
    return [
        json.dumps(r, separators=("<br>", " = "), ensure_ascii=False)
        .replace('"', "")
        .replace("{", "")
        .replace("}", "")
        for r in df.to_dict(orient="records")
    ]
