"""Unittests for ptxboa api_data module."""

from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd
import pytest

from ptxboa.api_data import (
    DEFAULT_DATA_DIR,
    STATIC_DATA_DIR,
    DataHandler,
    ScenarioValues,
    _load_scenario_data,
)
from ptxboa.static import ChainType, ChainValues, TransportType
from ptxboa.static._type_defs import ChainDef
from tests.utils import assert_deep_equal_approx


@pytest.fixture()
def user_data_01():
    return pd.DataFrame(
        data=[
            ("Australia", "PV tilted", 800, "CAPEX", None),
            ("Chile", "PV tilted", 900, "CAPEX", None),
            ("Chile", "Wind Offshore", 5000, "full load hours", None),
            ("Argentina", "PV tilted", 2000, "full load hours", None),
            ("Costa Rica", "Wind-PV-Hybrid", 2000, "full load hours", None),
            ("Australia", "Wind Onshore", 4000, "full load hours", None),
            ("Costa Rica", None, 0.12, "WACC", None),
        ],
        columns=[
            "source_region_code",
            "process_code",
            "value",
            "parameter_code",
            "flow_code",
        ],
    )


@pytest.fixture()
def ptxdata_dir_static():
    """Instance with static copy of the data, this dataset will never change."""
    return Path(__file__).parent / "test_data"


@pytest.fixture()
def ptxdata_dir_live():
    """
    Instance with live data as used in deployment.

    This dataset could change and we might use this fixture to see if updates work
    correctly.
    """
    return None


@pytest.mark.parametrize(
    "scenario, parameter_code, process_code, flow_code, source_region_code, target_country_code, process_res, process_ely, process_deriv, user_data, expected, default",  # noqa
    (
        (
            "2030 (low)",  # scenario
            "CALOR",  # parameter_code
            "",  # process_code
            "CH3OH-L",  # flow_code
            "",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_ely
            "",  # process_deriv
            None,  # user_data
            5.527777777777777,  # expected
            None,  # default
        ),
        (
            "2030 (low)",  # scenario
            "CALOR",  # parameter_code
            "",  # process_code
            "CH3OH-L",  # flow_code
            "",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_ely
            "",  # process_deriv
            "user_data_01",  # user_data
            5.527777777777777,  # expected
            None,  # default
        ),
        (
            "2030 (low)",  # scenario
            "CAPEX",  # parameter_code
            "PV-FIX",  # process_code
            "",  # flow_code
            "AUS",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_ely
            "",  # process_deriv
            None,  # user_data
            595.0020882465886,  # expected
            None,  # default
        ),
        (
            "2030 (low)",  # scenario
            "CAPEX",  # parameter_code
            "PV-FIX",  # process_code
            "",  # flow_code
            "AUS",  # source_region_code
            "",  # target_country_code
            "",  # process_code
            "",  # process_ely
            "",  # process_deriv
            "user_data_01",  # user_data
            800,  # expected
            None,  # default
        ),
        (
            "2030 (low)",  # scenario
            "FLH",  # parameter_code
            "PV-TRK",  # process_code
            "",  # flow_code
            "SWE",  # source_region_code
            "",  # target_country_code
            "PEM-EL",  # process_code
            "",  # process_ely
            "",  # process_deriv
            None,  # user_data
            8760,  # expected: default value
            8760,  # default
        ),
    ),
)
@pytest.mark.parametrize("ptxdata_dir", ("ptxdata_dir_static",))
def test_get_parameter_value(
    ptxdata_dir,
    scenario,
    parameter_code,
    process_code,
    flow_code,
    source_region_code,
    target_country_code,
    process_res,
    process_ely,
    process_deriv,
    user_data,
    expected,
    request,
    default,
):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)

    if user_data is not None:
        user_data = request.getfixturevalue(user_data)

    data_handler = DataHandler(
        scenario=scenario, user_data=user_data, data_dir=ptxdata_dir
    )
    result = data_handler._get_parameter_value(
        parameter_code=parameter_code,
        process_code=process_code,
        flow_code=flow_code,
        source_region_code=source_region_code,
        target_country_code=target_country_code,
        process_res=process_res,
        process_ely=process_ely,
        process_deriv=process_deriv,
        default=default,
    )

    assert_deep_equal_approx(expected, result, allow_new_dict_items=True)


@pytest.mark.parametrize(
    "dimension, parameter_name, expected_code",
    (
        ("country", "Germany", "DEU"),
        ("country", "", ""),
        ("country", None, ""),
        ("secproc_water", "Specific costs", ""),
    ),
)
def test_get_dimensions_parameter_code(dimension, parameter_name, expected_code):
    out_code = DataHandler.get_dimensions_parameter_code(dimension, parameter_name)
    assert out_code == expected_code


@pytest.mark.parametrize(
    "ptxdata_dir, scenario, kwargs",
    [
        [
            "ptxdata_dir_static",
            "2040 (medium)",
            {
                "source_region_code": "ARE",
                "target_country_code": "DEU",
                "chain_name": "Ammonia (AEL) + reconv. to H2",
                "process_res": "PV-FIX",
                "secondary_processes": {"H2O-L": "DESAL"},
                "ship_own_fuel": False,
                "transport": "Ship",
            },
        ],
    ],
)
def test_get_calculation_data(ptxdata_dir, scenario, kwargs, request):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)
    data_handler = DataHandler(data_dir=ptxdata_dir, scenario=scenario)
    data = data_handler.get_calculation_data(ChainDef(**kwargs), optimize_flh=False)

    assert_deep_equal_approx(
        {
            "flh_opt_process": {},
            "main_export_process_chain": [
                {
                    "EFF": 1,
                    "FLH": 1662.0,
                    "LIFETIME": 20.0,
                    "CAPEX": 334.7632213391997,
                    "OPEX-F": 5.690974762766395,
                    "OPEX-O": 0,
                    "CONV": {},
                    "step": "RES",
                    "process_code": "PV-FIX",
                },
                {
                    "EFF": 0.9,
                    "FLH": 7000,
                    "LIFETIME": 20.0,
                    "CAPEX": 888.7736990592965,
                    "OPEX-F": 0,
                    "OPEX-O": 0,
                    "CONV": {},
                    "step": "EL_STR",
                    "process_code": "EL-STR",
                },
                {
                    "EFF": 0.715,
                    "FLH": 2779.7,
                    "LIFETIME": 20.0,
                    "CAPEX": 862.3926136507007,
                    "OPEX-F": 17.247852273014015,
                    "OPEX-O": 0,
                    "CONV": {"H2O-L": 0.3},
                    "step": "ELY",
                    "process_code": "AEL-EL",
                },
                {
                    "EFF": 0.99,
                    "FLH": 7000,
                    "LIFETIME": 30.0,
                    "CAPEX": 40.24887553067399,
                    "OPEX-F": 0.5209021170671373,
                    "OPEX-O": 0,
                    "CONV": {},
                    "step": "H2_STR",
                    "process_code": "H2-STR",
                },
                {
                    "EFF": 0.819,
                    "FLH": 7752.95,
                    "LIFETIME": 30.0,
                    "CAPEX": 1519.4946618778151,
                    "OPEX-F": 75.97473309389076,
                    "OPEX-O": 0,
                    "CONV": {"EL": 0.1419230769230769, "N2-G": 0.1598076923076923},
                    "step": "DERIV",
                    "process_code": "NH3SYN",
                },
            ],
            "main_main_transport_process_chain": [
                {
                    "DIST": 12441.9,
                    "EFF": 0.9942580439718669,
                    "OPEX-T": 3.735743718162845e-07,
                    "OPEX-O": 0.0004856855350958,
                    "CONV": {"BFUEL-L": 5.343656103416341e-06},
                    "CONV-OT": {},
                    "step": "SHP",
                    "process_code": "NH3-SB",
                },
                {
                    "EFF": 0.7466101694915254,
                    "FLH": 6657.599999999999,
                    "LIFETIME": 25.0,
                    "CAPEX": 474.7596231401004,
                    "OPEX-F": 14.24278869420301,
                    "OPEX-O": 0,
                    "CONV": {"EL": 0.0076699999999999},
                    "step": "POST_SHP",
                    "process_code": "NH3-REC",
                },
            ],
            "main_import_process_chain": [],
            "secondary_process": {
                "H2O-L": {
                    "EFF": 1.0,
                    "FLH": 7000,
                    "LIFETIME": 20.0,
                    "CAPEX": 0.002731203678453,
                    "OPEX-F": 0.0001092481471381,
                    "OPEX-O": 0,
                    "CONV": {"EL": 0.003},
                    "process_code": "DESAL",
                }
            },
            "parameter": {
                "WACC": 0.0532,
                "SPECCOST": {
                    "BFUEL-L": 0.0032243376759515,
                    "CO2-G": 0.0445186199587845,
                    "EL": 0.08078,
                    "H2O-L": 0.0013737954502618,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                },
            },
            "parameter_import": {
                "WACC": 0.0532,
                "SPECCOST": {
                    "BFUEL-L": 0.0032243376759515,
                    "CO2-G": 0.0445186199587845,
                    "EL": 0.08078,
                    "H2O-L": 0.0013737954502618,
                    "HEAT": 0.0577,
                    "N2-G": 0.01154,
                },
            },
            "context": {"source_region_code": "ARE", "target_country_code": "DEU"},
        },
        data,
        allow_new_dict_items=True,
    )


@pytest.mark.parametrize(
    "ptxdata_dir, scenario, kwargs",
    [
        [
            "ptxdata_dir_static",
            "2040 (medium)",
            {
                "source_region_code": "ARG",
                "target_country_code": "DEU",
                "chain_name": "Ammonia (AEL) + reconv. to H2",
                "process_res": "RES-HYBR",
                "secondary_processes": {"H2O-L": "DESAL"},
                "ship_own_fuel": False,
                "transport": "Ship",
            },
        ],
    ],
)
def test_get_calculation_data_w_opt(ptxdata_dir, scenario, kwargs, request):
    ptxdata_dir = request.getfixturevalue(ptxdata_dir)

    with TemporaryDirectory() as cache_dir:
        # use temporary dir as cache dir
        data_handler = DataHandler(
            data_dir=ptxdata_dir, scenario=scenario, cache_dir=Path(cache_dir)
        )
        result = data_handler.get_calculation_data(
            ChainDef(**kwargs), optimize_flh=True
        )
    exp_result = {
        "flh_opt_process": {
            "PV-FIX": {
                "EFF": 1,
                "FLH": 1494.0,
                "LIFETIME": 20.0,
                "CAPEX": 503.2678018543936,
                "OPEX-F": 8.555552631524693,
                "OPEX-O": 0,
                "CONV": {},
            },
            "WIND-ON": {
                "EFF": 1,
                "FLH": 5369.0,
                "LIFETIME": 20.0,
                "CAPEX": 1046.9494493187117,
                "OPEX-F": 29.314584580923928,
                "OPEX-O": 0,
                "CONV": {},
            },
        },
        "main_export_process_chain": [
            {
                "EFF": 1,
                "FLH": 3041.279224698365,
                "LIFETIME": 20.0,
                "CAPEX": 855.8906210874661,
                "OPEX-F": 22.019513397327447,
                "OPEX-O": 0.0,
                "CONV": {},
                "step": "RES",
                "process_code": "RES-HYBR",
            },
            {
                "EFF": 0.9,
                "FLH": 7000,
                "LIFETIME": 20.0,
                "CAPEX": 888.7736990592965,
                "OPEX-F": 0,
                "OPEX-O": 0,
                "CONV": {},
                "step": "EL_STR",
                "process_code": "EL-STR",
                "CAP_F": 0.0,
            },
            {
                "EFF": 0.715,
                "FLH": 5058.623209737518,
                "LIFETIME": 20.0,
                "CAPEX": 862.3926136507007,
                "OPEX-F": 17.247852273014015,
                "OPEX-O": 0,
                "CONV": {"H2O-L": 0.3},
                "step": "ELY",
                "process_code": "AEL-EL",
            },
            {
                "EFF": 0.99,
                "FLH": 7000,
                "LIFETIME": 30.0,
                "CAPEX": 40.24887553067399,
                "OPEX-F": 0.5209021170671373,
                "OPEX-O": 0,
                "CONV": {},
                "step": "H2_STR",
                "process_code": "H2-STR",
                "CAP_F": 0.6816605398116187,
            },
            {
                "EFF": 0.819,
                "FLH": 7448.511114960053,
                "LIFETIME": 30.0,
                "CAPEX": 1519.4946618778151,
                "OPEX-F": 75.97473309389076,
                "OPEX-O": 0,
                "CONV": {"EL": 0.1419230769230769, "N2-G": 0.1598076923076923},
                "step": "DERIV",
                "process_code": "NH3SYN",
            },
        ],
        "main_main_transport_process_chain": [
            {
                "DIST": 12728.796,
                "EFF": 0.994125641025641,
                "OPEX-T": 3.735743718162845e-07,
                "OPEX-O": 0.0004856855350958,
                "CONV": {"BFUEL-L": 5.343656103416341e-06},
                "CONV-OT": {},
                "step": "SHP",
                "process_code": "NH3-SB",
            },
            {
                "EFF": 0.7466101694915254,
                "FLH": 6657.599999999999,
                "LIFETIME": 25.0,
                "CAPEX": 474.7596231401004,
                "OPEX-F": 14.24278869420301,
                "OPEX-O": 0,
                "CONV": {"EL": 0.0076699999999999},
                "step": "POST_SHP",
                "process_code": "NH3-REC",
            },
        ],
        "main_import_process_chain": [],
        "secondary_process": {
            "H2O-L": {
                "EFF": 1.0,
                "FLH": 5058.623209737517,
                "LIFETIME": 20.0,
                "CAPEX": 0.002731203678453,
                "OPEX-F": 0.0001092481471381,
                "OPEX-O": 0,
                "CONV": {"EL": 0.003},
                "process_code": "DESAL",
            }
        },
        "parameter": {
            "WACC": 0.2215019750791156,
            "SPECCOST": {
                "BFUEL-L": 0.0032243376759515,
                "CO2-G": 0.0445186199587845,
                "EL": 0.08078,
                "H2O-L": 0.0013737954502618,
                "HEAT": 0.0577,
                "N2-G": 0.01154,
            },
        },
        "parameter_import": {
            "WACC": 0.2215019750791156,
            "SPECCOST": {
                "BFUEL-L": 0.0032243376759515,
                "CO2-G": 0.0445186199587845,
                "EL": 0.08078,
                "H2O-L": 0.0013737954502618,
                "HEAT": 0.0577,
                "N2-G": 0.01154,
            },
        },
        "context": {"source_region_code": "ARG", "target_country_code": "DEU"},
        "flh_opt_hash": {
            "hash_md5": "10f4f69711354343d67b81a86ae20cf3",
        },
    }

    del result["flh_opt_hash"]["filepath"]  # dont test this

    assert_deep_equal_approx(exp_result, result, allow_new_dict_items=True)


@pytest.mark.parametrize(
    "chain",
    ChainValues,
)
@pytest.mark.parametrize(
    "transport, ship_own_fuel",
    [
        ("Pipeline", False),
        ("Ship", False),
        ("Ship", True),
    ],
)
def test_validate_chains(
    chain: ChainType,
    transport: TransportType,
    ship_own_fuel: bool,
):
    # skip test chain
    if chain == "Blue Iron (blue)*":
        return

    tool_version_color = DataHandler.get_chain_color(chain)
    process_res = "RES-HYBR" if (tool_version_color == "green") else None

    dh = DataHandler(
        scenario="2030 (medium)",
        tool_version_color=tool_version_color,
        # specifically DON'T use test data here
        # we want to validate the current chains
    )

    transport, ship_own_fuel = DataHandler.correct_transport(
        transport, ship_own_fuel, chain
    )

    # _validate_process_chain called inside here
    dh.get_calculation_data(
        ChainDef(
            secondary_processes={},
            chain_name=chain,
            process_res=process_res,
            source_region_code="ESP",
            target_country_code="DEU",
            transport=transport,
            ship_own_fuel=ship_own_fuel,
        ),
        optimize_flh=False,
    )


def test_parameter_data():
    """Test parameter data coverage.

    - test CONV parameter compared to expected flows in processes

    """
    # explicitly DONT use the DataHandler, but check raw csv data
    filepath_data = DEFAULT_DATA_DIR / "2030_medium.csv"
    filepath_process = STATIC_DATA_DIR / "dim_process.csv"

    df_data = pd.read_csv(filepath_data).fillna("")
    df_process = pd.read_csv(filepath_process).fillna("")

    # check: for each process, the secondary_flows should have a CONV parameter
    expected_conv_proc_flow: set[tuple[str, str]] = set()
    for _, proc in df_process.iterrows():
        secondary_flows = proc["secondary_flows"]
        if not isinstance(secondary_flows, str) or not secondary_flows:
            continue
        for flow_code in secondary_flows.split("/"):
            # TODO: CO2-C has no CONV, because it comes from captured CO2
            # so we ignore for now
            if flow_code == "CO2-C":
                continue
            expected_conv_proc_flow.add((proc["process_code"], flow_code))

    # get in data

    data_conv_proc_flow = {
        tuple(x)
        for x in df_data.loc[df_data["parameter_code"].isin({"CONV", "CONV-OT"})][
            ["process_code", "flow_code"]
        ].values
    }

    # compare

    missing_data = expected_conv_proc_flow - data_conv_proc_flow

    if missing_data:
        raise Exception("Missing CONV data for: %s", missing_data)

    unused_data = data_conv_proc_flow - expected_conv_proc_flow
    # known special cases (FIXME):
    unused_data = unused_data - {("H2-STR", "EL"), ("SYN-S", "CHX-L")}
    if unused_data:
        raise Exception("Unexpected CONV data for: %s", unused_data)


@pytest.mark.parametrize("year", ("2030", "2040"))
@pytest.mark.parametrize("cost_assumption", ("low", "medium", "high"))
@pytest.mark.parametrize(
    "dimension_column",
    ("parameter", "process", "flow", "source_region", "target_country"),
)
def test_dimension_values_exist_in_dimension_tables(
    year, cost_assumption, dimension_column
):
    """
    Verify that every dimension code exists in its corresponding dimension table.

    This ensures referential integrity between the main input data and the
    dimension metadata: no row in the input may reference a dimension value
    that is not explicitly defined. Each dimension type (process, flow, region,
    etc.) is validated against its respective lookup table.
    """
    # dim_name, dim_code
    dim_map = {
        "parameter": ("parameter", "parameter_code"),
        "process": ("process", "process_code"),
        "flow": ("flow", "flow_code"),
        # source_region checks the union of region + country
        "source_region": ("region_country", "region_country_code"),
        "target_country": ("country", "country_code"),
    }

    scenario = f"{year} ({cost_assumption})"
    handler = DataHandler(scenario=scenario)
    input_data = handler.get_input_data(long_names=False)

    dim_name, dim_code = dim_map[dimension_column]

    # Dimension table values
    if dim_name == "region_country":
        defined_values = handler.dimensions["region_country"][
            "region_country_code"
        ].unique()
    else:
        defined_values = handler.get_dimension(dim_name, tool_version_color=None)[
            dim_code
        ].unique()

    # Values encountered in the input
    values_in_data = (
        input_data[f"{dimension_column}_code"].replace("", pd.NA).dropna().unique()
    )

    undefined = sorted(set(values_in_data) - set(defined_values))

    assert not undefined, f"Undefined values for {dimension_column=} found: {undefined}"


@pytest.mark.parametrize("dimension", ("process", "flow", "region", "import_country"))
@pytest.mark.parametrize(
    "parameter_code",
    pd.read_csv(STATIC_DATA_DIR / "dim_parameter.csv")["parameter_code"].tolist(),
)
@pytest.mark.parametrize("cost_assumption", ("low", "medium", "high"))
@pytest.mark.parametrize("year", ("2030", "2040"))
def test_parameter_restricts_usage_to_allowed_dimensions(
    year, cost_assumption, parameter_code, dimension
):
    """
    Ensure that parameters only use dimensions for which they are marked as allowed.

    According to the parameter specification, some parameters are not permitted
    to vary by specific dimensions (e.g., process, flow, region). For such
    parameters, the associated dimension-code fields in the input dataset must
    remain empty. This test verifies that the dataset does not assign values
    in forbidden dimensions for any parameter.
    """
    dim_col_map = {
        "process": "process_code",
        "flow": "flow_code",
        "region": "source_region_code",
        "import_country": "target_country_code",
    }

    scenario = f"{year} ({cost_assumption})"
    handler = DataHandler(scenario=scenario)
    input_data = handler.get_input_data(long_names=False)

    # Get parameter spec
    param_table = handler.get_dimension("parameter", tool_version_color=None)
    param_spec = param_table.loc[[parameter_code], :].to_dict("records")[0]
    allowed = param_spec[f"per_{dimension}"]

    if not allowed:
        # Filter data for this parameter only
        df_param = input_data.loc[input_data["parameter_code"] == parameter_code]
        # No data for this parameter: test_parameter_data_present will check this
        if df_param.empty:
            return
        dim_col = dim_col_map[dimension]
        dim_values = df_param[dim_col].unique()
        non_empty = sorted(v for v in dim_values if v != "")
        assert not non_empty, (
            f"Parameter {parameter_code} is not allowed per {dimension}, "
            f"but has non-empty values: {non_empty}"
        )


@pytest.mark.parametrize(
    "parameter_code",
    pd.read_csv(STATIC_DATA_DIR / "dim_parameter.csv")["parameter_code"].tolist(),
)
@pytest.mark.parametrize("cost_assumption", ("low", "medium", "high"))
@pytest.mark.parametrize("year", ("2030", "2040"))
def test_parameter_has_data(year, cost_assumption, parameter_code):
    """
    Check that every parameter has at least one record in the input dataset.

    Every parameter defined in the parameter dimension table must appear in the
    input data. Missing parameter entries indicate incomplete or inconsistent
    dataset preparation. This test ensures that no parameter is silently
    omitted.
    """
    scenario = f"{year} ({cost_assumption})"
    data_handler = DataHandler(scenario=scenario)
    input_data = data_handler.get_input_data(long_names=False)
    parameter_data = input_data.loc[input_data["parameter_code"] == parameter_code]
    if len(parameter_data) == 0:
        pytest.fail(f"No data defined for {parameter_code=}")


def test_chains():
    # check known columns in chain
    df_chain = DataHandler.get_dimension("chain")
    df_process = DataHandler.get_dimension("process")
    df_flow = DataHandler.get_dimension("flow")

    COLS_PROC_MAIN_CHAIN = [
        "NG_PROD",
        "EL_STR",
        "ELY",
        "H2_STR",
        "DERIV",
        "DERIV2",
        "PRE_SHP",
        "SHP",
        "SHP_OWN",
        "POST_SHP",
        "PRE_PPL",
        "PPLS",
        "PPL",
        "PPLX",
        "PPLR",
        "POST_PPL",
        "ELY_I",
        "DERIV_I",
        "DERIV_I2",
    ]
    COLS_OTHER = [
        "chain",
        "chain_name",
        "flow_out",
        "can_pipeline",
        "is_green",
        "is_blue",
        "CO2_TS",
        "CO2_TS_I",
    ]

    expected_cols = set(COLS_PROC_MAIN_CHAIN + COLS_OTHER)
    cols = set(df_chain.columns)

    assert expected_cols == cols

    # for blue/green chains: find all used processes
    procs_res = set(df_process.loc[df_process["is_re_generation"], "process_code"])
    procs_green = (
        set(df_process.loc[df_process["is_green"], "process_code"]) - procs_res
    )
    procs_blue = set(df_process.loc[df_process["is_blue"], "process_code"])
    procs_sec = set(df_process.loc[df_process["is_secondary"], "process_code"])
    procs_all = set(df_process["process_code"])

    # assert no overlap
    assert not procs_green & procs_blue

    used_procs_green = set()
    used_procs_blue = set()
    for col in COLS_PROC_MAIN_CHAIN:
        used_procs_green = used_procs_green | set(
            df_chain.loc[(df_chain[col] != "") & df_chain["is_green"], col]
        )
        used_procs_blue = used_procs_blue | set(
            df_chain.loc[(df_chain[col] != "") & df_chain["is_blue"], col]
        )

    # check for proper subsets
    assert not used_procs_blue - procs_blue, used_procs_blue - procs_blue
    assert not used_procs_green - procs_green, used_procs_green - procs_green

    # check for unused/missing processes
    used_procs = used_procs_green | used_procs_blue | procs_sec | procs_res
    assert used_procs == procs_all, (used_procs - procs_all, procs_all - used_procs)

    # find all used flows
    used_flows = set()
    # combinations of process and flow
    used_process_flows = set()

    # ... per process
    for process_code, proc in df_process.iterrows():
        used_flows_proc = (
            {proc["main_flow_code_in"], proc["main_flow_code_out"]}
            | set(proc["secondary_flows"])
        ) - {""}
        used_flows = used_flows | used_flows_proc
        used_process_flows = used_process_flows | {
            (process_code, f) for f in used_flows_proc
        }

    flows = set(df_flow["flow_code"])

    assert used_flows == flows, (used_flows - flows, flows - used_flows)

    # check if in current data, we have combinations of process/flow that
    # is never used
    dfs = []
    for scen in ScenarioValues:
        df = _load_scenario_data(data_dir=DEFAULT_DATA_DIR, scenario=scen)
        dfs.append(df)
    df_data = pd.concat(dfs)
    data_proc_flow_combos = {
        tuple(x)
        for x in df_data.loc[
            (df_data["process_code"] != "") & (df_data["flow_code"] != ""),
            ["process_code", "flow_code"],
        ]
        .drop_duplicates()
        .values
    }
    unused_data_proc_flow_combos = data_proc_flow_combos - used_process_flows
    unused_data_proc_flow_combos = unused_data_proc_flow_combos - {
        ("H2-STR", "EL")  # FIXME (affects green tool)
    }
    print(unused_data_proc_flow_combos)
    assert not unused_data_proc_flow_combos, unused_data_proc_flow_combos
