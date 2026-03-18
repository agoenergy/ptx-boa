"""Tab with debugging output for blue version."""

import streamlit as st

from app.ptxboa_functions import calculate_cached


def content_debugging(api):
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
        ]
    }
    user_data = st.session_state["user_changes_df"]
    result = calculate_cached(
        api,
        secproc_water=st.session_state["secproc_water"],
        res_gen=st.session_state["res_gen"],
        user_data=user_data,
        optimize_flh=False,
        use_user_data_for_optimize_flh=False,
        tool_version_color="blue",
        **settings,
    )

    st.warning("Debugging output: will be removed in final version")

    st.subheader("Sidebar settings")
    st.json(settings)

    st.subheader("User data")
    if user_data is not None:
        st.dataframe(user_data)
    else:
        st.write(None)

    st.subheader("Calculation input data")
    st.json(result.todo_data)

    st.subheader("Flow results")
    st.json(result.todo_results_flows)

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
    st.subheader("Cost results")
    st.dataframe(result.costs.drop(columns=COLS_TO_DROP, errors="ignore"))

    st.subheader("Emission results")
    st.dataframe(
        result.emissions.drop(columns=COLS_TO_DROP, errors="ignore")
        if result.emissions is not None
        else None
    )

    st.subheader("Emission mass results")
    st.dataframe(
        result.emission_mass.drop(columns=COLS_TO_DROP, errors="ignore")
        if result.emission_mass is not None
        else None
    )
