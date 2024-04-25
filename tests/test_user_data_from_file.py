# -*- coding: utf-8 -*-
"""Functions for testing user data upload validation."""

from pathlib import Path

import pandas as pd
import pytest

from app.user_data_from_file import _read_user_data_file, _validate_user_dataframe
from ptxboa import DEFAULT_DATA_DIR
from ptxboa.api import PtxboaAPI

user_data_dir = Path(__file__).parent / "test_user_data"


@pytest.fixture()
def valid_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "valid_user_data.csv")


@pytest.fixture()
def wrong_column_name_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "wrong_column_name_user_data.csv")


@pytest.fixture()
def too_many_columns_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "too_many_columns_user_data.csv")


@pytest.fixture()
def non_existent_index_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "non_existent_index_user_data.csv")


@pytest.fixture()
def non_numeric_empty_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "non_numeric_empty_user_data.csv")


@pytest.fixture()
def non_numeric_string_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "non_numeric_string_user_data.csv")


@pytest.fixture()
def non_numeric_nan_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "non_numeric_nan_user_data.csv")


@pytest.fixture()
def param_below_range_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "param_below_range_user_data.csv")


@pytest.fixture()
def param_above_range_user_data() -> pd.DataFrame:
    return _read_user_data_file(user_data_dir / "param_above_range_user_data.csv")


@pytest.mark.parametrize(
    "user_data, expected_result",
    (
        ("valid_user_data", "valid_user_data"),
        (
            "wrong_column_name_user_data",
            "column names must be ['flow_code', 'parameter_code', 'process_code', 'source_region_code', 'value']",  # noqa
        ),
        (
            "too_many_columns_user_data",
            "column names must be ['flow_code', 'parameter_code', 'process_code', 'source_region_code', 'value']",  # noqa
        ),
        (
            "non_existent_index_user_data",
            "invalid index combination 'India | Ammonia Synthesis (Haber-Bosch) | efficiency | '",  # noqa
        ),
        (
            "non_numeric_empty_user_data",
            "non numeric values in 'value' column.",
        ),
        (
            "non_numeric_nan_user_data",
            "non numeric values in 'value' column.",
        ),
        (
            "non_numeric_string_user_data",
            "non numeric values in 'value' column.",
        ),
        (
            "param_below_range_user_data",
            "'OPEX (fix)' needs to be in range [0, inf] but is -100.0.",
        ),
        (
            "param_above_range_user_data",
            "'full load hours' needs to be in range [0, 8760] but is 10000.0.",
        ),
    ),
)
def test_validate_user_dataframe(user_data, expected_result, request):
    api = PtxboaAPI(data_dir=DEFAULT_DATA_DIR)
    user_data = request.getfixturevalue(user_data)

    if expected_result == "valid_user_data":
        expected_result = request.getfixturevalue(expected_result)

    result = _validate_user_dataframe(
        api=api, scenario="2040 (medium)", result=user_data
    )

    if isinstance(expected_result, pd.DataFrame):
        pd.testing.assert_frame_equal(result, expected_result)
    else:
        assert result == expected_result
