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
)
from ptxboa.api import PtxboaAPI
from ptxboa.static import OutputUnitType, ScenarioType, TargetCountryNameType


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
def aggregate_green_results(
    _api: PtxboaAPI,
    scenarios: list[ScenarioType],
    import_country: TargetCountryNameType,
    output_product: str,
    output_unit: OutputUnitType,
    green_param_set: Literal["restricted", "complete"] = "restricted",
):

    if output_product not in [
        "NH3-L",
        "DRI-S",
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
                    _api.get_dimension("chain", tool_version_color="green")["FLOW_OUT"]
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
                    _api.get_dimension("chain", tool_version_color="green")["FLOW_OUT"]
                    == output_product
                ]
                .index.tolist()
            ),
        }
    else:
        raise ValueError(f"Unknown {green_param_set=}")

    stats = []

    for scenario in scenarios:
        costs = []
        for param_set in list(product_dict(**dimensions)):
            try:
                costs.append(
                    calculate_cached(
                        _api,
                        user_data=None,  # we do not respect user data here
                        optimize_flh=False,  # TODO revert to True when ready
                        use_user_data_for_optimize_flh=False,
                        scenario=scenario,
                        country=import_country,
                        output_unit=output_unit,
                        tool_version_color="blue",
                        **param_set,
                    )
                    .costs["values"]
                    .sum()
                )
            except Exception as exc:
                logging.info(f"could not get data: {exc}")
        stats.append(
            pd.Series(costs)
            .describe()
            .rename("values")
            .rename_axis(index="metric")
            .reset_index()
            .assign(scenario=scenario)
        )

    return pd.concat(stats).pivot(columns="metric", index="scenario", values="values")


def get_data(
    api, scenarios: list[ScenarioType], import_country, output_product, output_unit
):
    with st.spinner("Calculating green results"):
        costs_green = aggregate_green_results(
            api,
            scenarios=scenarios,
            import_country=import_country,
            output_product=output_product,
            output_unit=output_unit,
        )

    costs_blue = calculate_results_list_blue(
        api,
        parameter_to_change="scenario",
        parameter_list=scenarios,
        apply_user_data=True,
        override_session_state=None,
    )[0].add_prefix("blue_")

    return pd.concat([costs_green, costs_blue], axis=1).reset_index()


def make_figure(
    data: pd.DataFrame,
    x,
    green_median,
    green_lower_bound,
    green_upper_bound,
    blue,
    output_product_label: str,
    xaxis_title: str,
    yaxis_title: str,
) -> go.Figure:
    GREEN_COLOR = "#2fac66"
    BLUE_COLOR = "#1E83B3"
    BOUNDS_LW = 0.7

    def _add_invisible_trace(fig, df, x, y):
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[y],
                fill=None,
                mode="lines",
                line_color="rgba(0,0,0,0)",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    def _add_line(
        fig,
        df,
        x,
        y,
        line_color,
        legend_label,
        hover_label,
        showlegend,
        fill,
        **kwargs,
    ):
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[y],
                fill=fill,
                mode="lines",
                line_color=line_color,
                showlegend=showlegend,
                name=legend_label,
                hoverinfo="text",
                hovertext=[f"{hover_label}: {v}" for v in df[y]],
                **kwargs,
            )
        )

    fig = go.Figure()

    # fill='tonexty' always references trace which was added before
    _add_invisible_trace(fig=fig, df=data, x=x, y=green_median)
    _add_line(
        fig=fig,
        df=data,
        legend_label=f"25th - 75th percentile green {output_product_label}",
        hover_label=f"75th percentile green {output_product_label}",
        x=x,
        y=green_upper_bound,
        line_color=GREEN_COLOR,
        line={"width": BOUNDS_LW},
        fill="tonexty",
        showlegend=True,
    )

    _add_line(
        fig=fig,
        df=data,
        legend_label=f"Median green {output_product_label}",
        hover_label=f"Median green {output_product_label}",
        x=x,
        y=green_median,
        line_color=GREEN_COLOR,
        fill=None,
        showlegend=True,
    )

    _add_line(
        fig=fig,
        df=data,
        legend_label=f"25th - 75th percentile green {output_product_label}",
        hover_label=f"25th percentile green {output_product_label}",
        x=x,
        y=green_lower_bound,
        line_color=GREEN_COLOR,
        line={"width": BOUNDS_LW},
        fill="tonexty",
        showlegend=False,
    )

    _add_line(
        fig=fig,
        df=data,
        legend_label=f"Blue {output_product_label}",
        hover_label=f"Blue {output_product_label}",
        x=x,
        y=blue,
        line_color=BLUE_COLOR,
        fill=None,
        showlegend=True,
    )

    fig.update_layout(
        hovermode="x unified",
        legend_traceorder="reversed",
        xaxis={"title": {"text": xaxis_title}},
        yaxis={"title": {"text": yaxis_title}},
    )
    return fig


def crude_steel_warning():
    st.warning(
        "Cannot compare crude steel with available green PtX output products."
        " Please use iron instead."
    )


def content_costs_comparison(api):
    with st.popover("*Help*", width="stretch"):
        st.markdown("User data not used to optimize FLH for green costs.")

    with st.container(border=True):
        if st.session_state["output_product"] == "STL-S":
            crude_steel_warning()
            return

        costs = get_data(
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
        fig = make_figure(
            costs,
            x="scenario",
            green_median="50%",
            green_lower_bound="25%",
            green_upper_bound="75%",
            blue="blue_Total",
            output_product_label=st.session_state["output_product_label"],
            xaxis_title="Scenario",
            yaxis_title=st.session_state["output_unit"],
        )
        st.plotly_chart(fig)
