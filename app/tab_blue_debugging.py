"""Tab with debugging output for blue version."""

import json
from typing import Any, Callable, Literal

import pandas as pd
import streamlit as st

from app.ptxboa_functions import calculate_cached
from ptxboa.static._type_defs import ApiCalculateResult

Mode = Literal["markdown", "streamlit_app"]
Renderer = Callable[[Any, Mode], str | None]


COLS_TO_DROP = [
    "chain",
    "country",
    "output_unit",
    "region",
    "scenario",
    "secproc_co2",
    "ship_own_fuel",
    "transport",
    "secproc_water",
    "res_gen",
]


def subheader_print(s: str, mode: Mode) -> str | None:
    if mode == "streamlit_app":
        st.subheader(s)
        return None
    elif mode == "markdown":
        return f"## {s}\n"
    raise ValueError(f"Unsupported mode: {mode}")


def none_print(mode: Mode) -> str | None:
    if mode == "streamlit_app":
        st.write(None)
        return None
    elif mode == "markdown":
        return "```python\nNone\n```\n"
    raise ValueError(f"Unsupported mode: {mode}")


def json_print(d: dict | None, mode: Mode) -> str | None:
    if d is None:
        return none_print(mode)

    if mode == "streamlit_app":
        st.json(d)
        return None
    elif mode == "markdown":
        return f"```json\n{json.dumps(d, indent=2, ensure_ascii=False)}\n```\n"
    raise ValueError(f"Unsupported mode: {mode}")


def dataframe_print(df: pd.DataFrame | None, mode: Mode) -> str | None:
    if df is None:
        return none_print(mode)

    if mode == "streamlit_app":
        st.dataframe(df)
        return None
    elif mode == "markdown":
        return (
            "```json\n"
            f"{df.to_json(orient='records', indent=2, force_ascii=False)}\n"
            "```\n"
        )
    raise ValueError(f"Unsupported mode: {mode}")


def drop_debug_columns(df: pd.DataFrame | None) -> pd.DataFrame | None:
    if df is None:
        return None
    return df.drop(columns=COLS_TO_DROP, errors="ignore")


def debug_report(
    result: ApiCalculateResult,
    user_data: pd.DataFrame | None,
    settings: dict[str, Any],
    mode: Mode,
) -> str | None:
    sections: list[tuple[str, Any, Renderer]] = [
        ("Sidebar settings", settings, json_print),
        ("User data", user_data, dataframe_print),
        (
            "Internal calculation input / result data",
            result._internal_process_data,
            json_print,
        ),
        ("Cost results", drop_debug_columns(result.costs), dataframe_print),
        (
            "Emission results",
            drop_debug_columns(result.emissions_t_co2e),
            dataframe_print,
        ),
        (
            "Emission mass results",
            drop_debug_columns(result.emission_mass_t_co2e),
            dataframe_print,
        ),
    ]

    report_parts: list[str] = []

    for title, value, renderer in sections:
        header = subheader_print(title, mode)
        if header is not None:
            report_parts.append(header)

        body = renderer(value, mode)
        if body is not None:
            report_parts.append(body)

    if mode == "markdown":
        content = "\n".join(report_parts)
        return f"# Debug Report\n\n{content}---\n"

    return None


def content_debugging(api: Any) -> None:
    required_keys = [
        "chain",
        "country",
        "output_unit",
        "region",
        "scenario",
        "secproc_co2",
        "ship_own_fuel",
        "transport",
        "secproc_water",
        "res_gen",
        "user_changes_df",
    ]

    missing_keys = [key for key in required_keys if key not in st.session_state]
    if missing_keys:
        st.error(f"Missing session state keys: {missing_keys}")
        return

    settings = {
        key: st.session_state[key]
        for key in [
            "chain",
            "country",
            "output_unit",
            "region",
            "scenario",
            "secproc_co2",
            "ship_own_fuel",
            "transport",
            "secproc_water",
            "res_gen",
        ]
    }

    user_data = st.session_state["user_changes_df"]

    result = calculate_cached(
        api,
        user_data=user_data,
        optimize_flh=False,
        use_user_data_for_optimize_flh=False,
        tool_version_color="blue",
        **settings,
    )

    st.warning("Debugging output: will be removed in final version")

    debug_report_md = debug_report(
        result=result,
        user_data=user_data,
        settings=settings,
        mode="markdown",
    )

    st.download_button(
        "Download debug report as markdown",
        data=debug_report_md,
        file_name="debug_log.md",
        mime="text/markdown",
    )

    debug_report(
        result=result,
        user_data=user_data,
        settings=settings,
        mode="streamlit_app",
    )
