"""Unittests for blue hydrogen version."""

import pandas as pd
import pytest

from ptxboa.api import _translate_and_validate_user_settings
from ptxboa.api_calc import PtxCalc
from ptxboa.api_data import DEFAULT_DATA_DIR, DataHandler
from ptxboa.static._type_defs import ChainDef
from tests.test_api import ptxdata_dir_static
from tests.utils import assert_deep_equal_approx


def _translate_user_data_inplace(user_data: pd.DataFrame) -> None:
    # NOTE: the columns say *_code,
    # but user data actually must be passed as names
    for colname in user_data.columns:
        if colname.endswith("_code"):
            user_data[colname] = user_data[colname].fillna("")

    for idx, row in user_data.iterrows():
        for colname, value in row.items():
            colname = str(colname)
            if value and colname.endswith("_code"):
                dimname = colname.replace("_code", "")
                basename = dimname.replace("target_", "").replace("source_", "")
                dim = DataHandler.dimensions[dimname]  # type: ignore
                try:
                    value = dim.loc[value, basename + "_name"]
                except Exception:
                    raise KeyError(
                        f"{colname}={value} not in {dimname}: "
                        f"{sorted(dim.index)}, {sorted(dim.columns)}"
                    )
                user_data.loc[idx, colname] = value  # type: ignore


# @pytest.mark.skip # noqa
@pytest.mark.parametrize(
    "scenario, kwargs, api_kwargs",
    [
        [
            "2040 (medium)",
            {
                "chain_name": "Blue Iron (blue)*",
                "source_region_code": "QAT",
                "target_country_code": "DEU",
                "process_res": None,
                "secondary_processes": {},
                "ship_own_fuel": False,
                "transport": "Ship",
            },
            {
                "region": "Qatar",
                "country": "Germany",
                "chain": "Blue Iron (blue)*",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
        ],
    ],
)
def test_new_blue_chain_fixed_data(scenario, kwargs, api_kwargs):
    """Data test for blue iron chain using test data."""
    user_data = pd.DataFrame(
        [
            {
                "parameter_code": "CAPEX",
                "process_code": "EAF#B",
                "value": 0.417344,
            },
            {
                "parameter_code": "OPEX-F",
                "process_code": "EAF#B",
                "value": 0.01252,
            },
            {
                "parameter_code": "OPEX-O",
                "process_code": "EAF#B",
                "value": 0.183679,
            },
            {
                "parameter_code": "CAPEX",
                "process_code": "NG-DRI-C#B",
                "value": 0.591876,
            },
            {
                "parameter_code": "OPEX-F",
                "process_code": "NG-DRI-C#B",
                "value": 0.017756,
            },
            {
                "source_region_code": "QAT",
                "parameter_code": "WACC",
                "value": 0,
            },
            {
                "source_region_code": "QAT",
                "target_country_code": "DEU",
                "parameter_code": "DST-S-D",
                "value": 999,
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "SPECCOST",
                "value": 0,
            },
            {
                "flow_code": "IOP-S",
                "parameter_code": "SPECCOST",
                "value": 0,
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "NG-G",  # main flow in
                "parameter_code": "LOSS",
                "value": 0.05,  # process_calc!E9
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "EFF",
                "value": 0.336004,  # process_calc!E3
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.476859,  # process_calc!E4
            },
            {
                "process_code": "NG-DRI-C#B",
                "flow_code": "IOP-S",
                "parameter_code": "CONV",
                "value": 1.373737,  # process_calc!E6
            },
            {
                "process_code": "EAF#B",
                "parameter_code": "LOSS",
                "flow_code": "NG-G",
                "value": 0.05,  # process_calc!J9
            },
            {
                "process_code": "EAF#B",
                "parameter_code": "EFF",
                "value": 1.010101,  # process_calc!J3
            },
            {
                "process_code": "EAF#B",
                "flow_code": "EL",
                "parameter_code": "CONV",
                "value": 0.651000,  # process_calc!J6
            },
            {
                "process_code": "EAF#B",
                "flow_code": "NG-G",
                "parameter_code": "CONV",
                "value": 0.004,  # process_calc!J4
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-S",
                "flow_code": "NG-G",
                "value": 0.45,  # process_calc!E11
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-S",
                "flow_code": "CH4-G",
                "value": 0.45,  # process_calc!E11
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-R",
                "flow_code": "NG-G",
                "value": 0.9,  # process_calc!E14
            },
            {
                "process_code": "NG-DRI-C#B",
                "parameter_code": "CO2CPT-R",
                "flow_code": "CH4-G",
                "value": 0.9,  # process_calc!E14
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CBOUND",
                "process_code": "NG-DRI-C#B",
                "value": 0.040812,  # process_calc!E17
            },
            {
                "flow_code": "NG-G",
                "parameter_code": "CH4SHARE",
                "value": 0.909,  # process_calc!E20
            },
            {
                "flow_code": "STL-S",
                "parameter_code": "CBOUND",
                "process_code": "EAF#B",
                "value": 0.00396,  # process_calc!J17
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "NG-G",
                "value": 201,  # emission_factors!D7
            },
            {
                "parameter_code": "EF_M",
                "flow_code": "CH4-G",
                "value": 201,  # emission_factors!I7
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "NG-G",
                "source_region_code": "QAT",
                "value": 201,  # emission_factors!D9
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "CH4-G",
                "value": 201,
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "EL",
                "source_region_code": "QAT",
                "value": 402,  # emission_factors!E9
            },
            {
                "parameter_code": "EF_E",
                "flow_code": "EL",
                "source_region_code": "DEU",
                "value": 300,  # emission_factors!F9
            },
        ]
    )
    _translate_user_data_inplace(user_data)

    # FIXME: this is a test chain and not (yet) marked as "blue" in data
    # so we need to fix it manually
    DataHandler.get_dimension("chain").loc["Blue Iron (blue)*", "is_blue"] = "True"

    data_handler = DataHandler(
        data_dir=ptxdata_dir_static,
        scenario=scenario,
        user_data=user_data,
        tool_version_color="blue",
    )

    chain_def = ChainDef(**kwargs)
    ptx_calc = PtxCalc.get_or_create(chain_def)

    calculation_data = data_handler.get_calculation_data(
        ptx_calc=ptx_calc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=False,
    )
    ptxcalc_results = ptx_calc.calculate(data=calculation_data)

    expected = {
        "df_results_cost": [
            {
                "cost_type": "CAPEX",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 2.98e-06,
            },
            {
                "cost_type": "FLOW",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 0.05258778,
            },
            {
                "cost_type": "OPEX",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 0.18368079,
            },
            {
                "cost_type": "CAPEX",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 4.19e-06,
            },
            {
                "cost_type": "FLOW",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 0.03813546,
            },
            {
                "cost_type": "OPEX",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 2.51e-06,
            },
        ],
        "df_results_emissions_e_g_co2e": [
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 0.3724882,
            },
            {
                "emission_type": "indirect",
                "gas_type": "CO2",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 195.3,
            },
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 274.37420694,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 204.31608375,
            },
            {
                "emission_type": "indirect",
                "gas_type": "CO2",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 189.78034672,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "DRI-SB#B",
                "process_type": "Transportation (Ship)",
                "values": 148.05784985,
            },
        ],
        "df_results_emissions_m_g_co2e": [
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 0.3724882,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "EAF#B",
                "process_type": "Derivative production",
                "values": 0.804,
            },
            {
                "emission_type": "direct",
                "gas_type": "CH4",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 274.37420694,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "NG-DRI-C#B",
                "process_type": "Derivative production",
                "values": 204.31608375,
            },
            {
                "emission_type": "direct",
                "gas_type": "CO2",
                "process_subtype": "DRI-SB#B",
                "process_type": "Transportation (Ship)",
                "values": 148.05784985,
            },
        ],
        "results_flows_chain": [
            {
                "main_flow_out": 3.0937132,
                "process_code": "NG-PROD#B",
                "step": "NG_PROD",
            },
            {
                "main_flow_in": 3.0937132,
                "main_flow_out": 0.99000001,
                "process_code": "NG-DRI-C#B",
                "secondary_flows_in": {
                    "CO2-C": 0.23985116,
                    "EL": 0.47209041,
                    "IOP-S": 1.35999964,
                },
                "step": "DERIV",
            },
            {
                "main_flow_in": 0.99000001,
                "main_flow_out": 0.99000001,
                "process_code": "DRI-SB#B",
                "step": "SHP",
            },
            {
                "main_flow_in": 0.99000001,
                "main_flow_out": 1,
                "process_code": "EAF#B",
                "secondary_flows_in": {"EL": 0.651, "NG-G": 0.0042},
                "step": "DERIV_I",
            },
        ],
    }

    assert_deep_equal_approx(expected, ptxcalc_results, sort_list_by_keys=["step"])


@pytest.mark.parametrize(
    "api_kwargs,expected",
    [
        # =============================================================================
        # CASE 1
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Qatar",
                "country": "Germany",
                "chain": "CHX-L__EFUELSYNC__prod_in_supply",
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "df_results_cost": [
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "EFUELSYNC#B",
                        "process_type": "Derivative production",
                        "values": 0.00952357,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "EFUELSYNC#B",
                        "process_type": "Derivative production",
                        "values": 0.00298571,
                    },
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.00025356,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.00010475,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 4.617e-05,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.00880988,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "SYN-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 5.23e-05,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "SYN-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00057767,
                    },
                ],
                "df_results_emissions_e_g_co2e": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EFUELSYNC#B",
                        "process_type": "Derivative production",
                        "values": 10.21118998,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.4679766,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.28735533,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "SYN-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 266.76000002,
                    },
                ],
                "df_results_emissions_m_g_co2e": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EFUELSYNC#B",
                        "process_type": "Derivative production",
                        "values": 10.21118998,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.4679766,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.28735533,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "SYN-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 271.50715383,
                    },
                ],
                "results_flows_chain": [
                    {
                        "main_flow_out": 1.81177628,
                        "process_code": "NG-PROD#B",
                        "secondary_flows_in": {"DIESEL-L": 0.00107721},
                        "step": "NG_PROD",
                    },
                    {
                        "main_flow_in": 1.789,
                        "main_flow_out": 1.0,
                        "process_code": "EFUELSYNC#B",
                        "secondary_flows_in": {"CO2-C": 0.08261781, "EL": 0.0115},
                        "step": "DERIV",
                    },
                    {
                        "main_flow_in": 1.0,
                        "main_flow_out": 1,
                        "process_code": "SYN-SB#B",
                        "secondary_flows_in": {"BFUEL-L": 0.0162196},
                        "step": "SHP",
                    },
                ],
                "results_flows_secondary": [
                    {
                        "main_flow_in": 0.09129249,
                        "main_flow_out": 0.08672787,
                        "process_code": "CO2-T+S#B",
                    },
                    {
                        "main_flow_in": 0.02277628,
                        "main_flow_out": 0.0115,
                        "process_code": "CCGT-CC#B",
                        "secondary_flows_in": {"CO2-C": 0.00411006},
                    },
                ],
            },
            # marks=pytest.mark.skip,  # noqa
        ),
        # =============================================================================
        # CASE 2
        # ==============================================================================
        pytest.param(
            {
                "scenario": "2040 (medium)",
                "region": "Algeria",
                "country": "Germany",
                "chain": "STL-S__NG-DRI-C_EAF__prod_in_demand",  # sheet 41
                "res_gen": None,
                "transport": "Ship",
                "ship_own_fuel": False,
                "secproc_co2": "Direct Air Capture (blue)",
                "secproc_water": "Sea Water desalination",
            },
            {
                "df_results_cost": [
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "CO2-T+S#B",
                        "process_type": "CO2 transport and storage",
                        "values": 0.03547894,
                    },
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 4.48e-06,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 0.07426958,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 0.18368048,
                    },
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 6.29e-06,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 0.41043233,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 2.51e-06,
                    },
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.00041145,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 7.357e-05,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 8.916e-05,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.01092275,
                    },
                    {
                        "cost_type": "CAPEX",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.02543352,
                    },
                    {
                        "cost_type": "OPEX",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00343556,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.00021823,
                    },
                    {
                        "cost_type": "FLOW",
                        "process_subtype": "CH4-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 9.952e-05,
                    },
                ],
                "df_results_emissions_e_g_co2e": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "Bound in product",
                        "process_type": "Bound in product",
                        "values": 14.65778518,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 193.69866408,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 65.1,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 204.31789996,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 47.209,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.32870807,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.55495967,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 3.1663146,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 690.62804877,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 1.9e-07,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 592.73076089,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.14142706,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 592.225797,
                    },
                ],
                "df_results_emissions_m_g_co2e": [
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "Bound in product",
                        "process_type": "Bound in product",
                        "values": 14.65778518,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 193.69866408,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "EAF#B",
                        "process_type": "Derivative production",
                        "values": 65.1,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 204.31789996,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "NG-DRI-C#B",
                        "process_type": "Derivative production",
                        "values": 47.209,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CCGT-CC#B",
                        "process_type": "Electricity generation",
                        "values": 0.32870807,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "NG-PROD#B",
                        "process_type": "Natural gas production",
                        "values": 0.55495967,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 3.1663146,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-LIQ#B",
                        "process_type": "Transportation (Ship)",
                        "values": 690.62804877,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CH4",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 1.9e-07,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 592.73076089,
                    },
                    {
                        "emission_type": "indirect",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-RGAS#B",
                        "process_type": "Transportation (Ship)",
                        "values": 0.14142706,
                    },
                    {
                        "emission_type": "direct",
                        "gas_type": "CO2",
                        "process_subtype": "CH4-SB#B",
                        "process_type": "Transportation (Ship)",
                        "values": 601.25934642,
                    },
                ],
                "results_flows_chain": [
                    {
                        "main_flow_out": 3.45367654,
                        "process_code": "NG-PROD#B",
                        "secondary_flows_in": {"DIESEL-L": 0.00208037},
                        "step": "NG_PROD",
                    },
                    {
                        "main_flow_in": 3.43767842,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-LIQ#B",
                        "secondary_flows_in": {"EL": 0.00807763},
                        "step": "PRE_SHP",
                    },
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-SB#B",
                        "secondary_flows_in": {"BFUEL-L": 0.03086494},
                        "step": "SHP",
                    },
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 2.946397,
                        "process_code": "CH4-RGAS#B",
                        "secondary_flows_in": {
                            "DIESEL-L": 5.89e-06,
                            "EL": 0.00141427,
                            "NG-G": 0.00250444,
                        },
                        "step": "POST_SHP",
                    },
                    {
                        "main_flow_in": 2.946397,
                        "main_flow_out": 0.99,
                        "process_code": "NG-DRI-C#B",
                        "secondary_flows_in": {
                            "CO2-C": 0.23985145,
                            "EL": 0.47209,
                            "IOP-S": 1.36,
                        },
                        "step": "DERIV_I",
                    },
                    {
                        "main_flow_in": 0.99,
                        "main_flow_out": 1,
                        "process_code": "EAF#B",
                        "secondary_flows_in": {"EL": 0.651, "NG-G": 0.3},
                        "step": "DERIV_I2",
                    },
                ],
                "results_flows_secondary": [
                    {
                        "main_flow_in": 0.25247521,
                        "main_flow_out": 0.23985145,
                        "process_code": "CO2-T+S#B",
                    },
                    {
                        "main_flow_in": 0.00303886,
                        "main_flow_out": 0.00288691,
                        "process_code": "CO2-T+S#B",
                    },
                    {
                        "main_flow_in": 0.01599812,
                        "main_flow_out": 0.00807763,
                        "process_code": "CCGT-CC#B",
                        "secondary_flows_in": {"CO2-C": 0.00288691},
                    },
                ],
            },
            # marks=pytest.mark.skip,  # noqa
        ),
    ],
)
def test_new_blue_chain_real_data(api_kwargs, expected):
    """Data test for blue iron chain using current data."""
    # test api output

    # validate and translate user settings
    chain_def, tool_version_color, optimize_flh = _translate_and_validate_user_settings(
        **api_kwargs
    )

    data_handler = DataHandler(
        data_dir=DEFAULT_DATA_DIR,
        scenario=api_kwargs["scenario"],
        tool_version_color=tool_version_color,
    )
    ptx_calc = PtxCalc.get_or_create(chain_def)

    data = data_handler.get_calculation_data(
        ptx_calc=ptx_calc,
        source_region_code=chain_def.source_region_code,
        target_country_code=chain_def.target_country_code,
        optimize_flh=optimize_flh,
    )

    # calculate results
    ptxcalc_result = ptx_calc.calculate(data)  # NEW # noqa

    assert_deep_equal_approx(
        expected,
        ptxcalc_result,
        allow_new_dict_items=True,
        sort_list_by_keys=[
            "step",
            "process_type",
            "process_subtype",
            "cost_type",
            "emissionemission_type",
            "gas_type",
        ],
    )
