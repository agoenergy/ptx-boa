# -*- coding: utf-8 -*-
"""Content of input data tab."""
import plotly.express as px
import streamlit as st
import streamlit_antd_components as sac

from app.layout_elements import (
    display_and_edit_input_data,
    display_costs,
    what_is_a_boxplot,
)
from app.plot_functions import plot_costs_on_map, plot_input_data_on_map
from app.ptxboa_functions import (
    costs_over_dimension,
    read_markdown_file,
    select_subregions,
)
from ptxboa.api import PtxboaAPI


def content_deep_dive_countries(api: PtxboaAPI) -> None:
    """Create content for the "costs by region" sheet.

    Parameters
    ----------
    api : :class:`~ptxboa.api.PtxboaAPI`
        an instance of the api class
    costs_per_region : pd.DataFrame
        Results.

    Output
    ------
    None
    """
    with st.popover("*Help*", use_container_width=True):
        st.markdown(read_markdown_file("md/whatisthis_deep_dive_countries.md"))

    st.write("Select which country to display:")
    ddc = sac.buttons(
        items=[
            sac.ButtonsItem(label="Argentina"),
            sac.ButtonsItem(label="Morocco"),
            sac.ButtonsItem(label="South Africa"),
        ],
        use_container_width=True,
    )

    with st.spinner("Please wait. Calculating results for different source regions"):
        costs_per_region, costs_per_region_without_user_changes = costs_over_dimension(
            api,
            dim="region",
            parameter_list=[
                x for x in api.get_dimension("region").index if x.startswith(f"{ddc} (")
            ],
        )

    with st.container(border=True):
        st.subheader("Costs per subregion")
        fig_map = plot_costs_on_map(
            api, costs_per_region, scope=ddc, cost_component="Total"
        )
        st.plotly_chart(fig_map, use_container_width=True)

        st.divider()

        display_costs(
            select_subregions(costs_per_region, ddc),
            (
                select_subregions(costs_per_region_without_user_changes, ddc)
                if st.session_state["user_changes_df"] is not None
                else None
            ),
            key="region",
            titlestring="Costs per subregion",
            key_suffix=ddc,
        )

    with st.container(border=True):
        st.subheader("Full load hours of renewable generation")

        # in order to keep the figures horizontally aligned, we create two st.columns
        # pairs, the columns are identified by c_{row}_{column}, zero indexed
        c_0_0, c_0_1 = st.columns([2, 1], gap="large")
        c_1_0, c_1_1 = st.columns([2, 1], gap="large")
        with c_0_0:
            st.markdown("**Map**")
            map_parameter = st.selectbox(
                "Show parameter on map",
                [
                    "Wind Onshore",
                    "Wind Offshore",
                    "PV tilted",
                    "Wind Onshore (hybrid)",
                    "PV tilted (hybrid)",
                ],
                key="ddc_flh_map_parameter",
            )
        with c_1_0:
            fig = plot_input_data_on_map(
                api=api,
                data_type="full load hours",
                color_col=map_parameter,
                scope=ddc,
            )
            st.plotly_chart(fig, use_container_width=True)
        with st.expander("**Data**"):
            df = display_and_edit_input_data(
                api,
                data_type="full load hours",
                scope=ddc,
                key=f"input_data_full_load_hours_{ddc.replace(' ', '_').lower()}",
            )

        with c_0_1:
            st.markdown("**Regional distribution**")
        with c_1_1:
            fig = px.box(
                df,
                hover_data=[df.index],
                hover_name="res_gen",
            )
            fig.update_layout(xaxis_title=None)
            st.plotly_chart(fig, use_container_width=True)
            what_is_a_boxplot()
