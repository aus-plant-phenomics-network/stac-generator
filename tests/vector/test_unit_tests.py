from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

import pandas as pd
import pystac
import pytest

from stac_generator.core.base.utils import read_source_config
from stac_generator.core.vector.generator import VectorGenerator
from stac_generator.exceptions import StacConfigException

CONFIG_PATH = Path("tests/files/unit_tests/vectors/configs")


@lru_cache
def load_items(file: str) -> Sequence[pystac.Item]:
    config_path = CONFIG_PATH / file
    configs = read_source_config(str(config_path))
    generators = [VectorGenerator(config) for config in configs]
    return [generator.generate() for generator in generators]


@lru_cache
def load_item(file: str) -> pystac.Item:
    return load_items(file)[0]


def run_join_nodate_test(
    item: pystac.Item, location: str, start: str, end: str, timestamps: list[str]
) -> None:
    assert item.properties["stac_generator"]["column_info"] == [
        {"name": "Suburb_Name", "description": "Suburb_Name"}
    ]
    assert item.properties["stac_generator"]["join_config"]["column_info"] == [
        {"name": "Area", "description": "Area name"},
        {"name": "Distance", "description": "Driving Distance to CBD in km"},
        {
            "name": "Public_Transport",
            "description": "Time taken to reach CBD by public transport in minutes",
        },
        {"name": "Drive", "description": "Time taken to reach CBD by driving in minutes"},
        {"name": "Growth", "description": "Average 5 year growth in percentage in 2025"},
        {"name": "Yield", "description": "Average rental yield in 2025"},
    ]
    assert item.properties["stac_generator"]["join_config"]["file"] == location
    assert item.properties["stac_generator"]["join_config"]["right_on"] == "Area"
    assert item.properties["stac_generator"]["join_config"]["left_on"] == "Suburb_Name"
    assert item.properties["start_datetime"] == start
    assert item.properties["end_datetime"] == end
    assert item.properties["timestamps"] == timestamps


def run_join_with_date_test(
    item: pystac.Item, location: str, start: str, end: str, timestamps: list[str]
) -> None:
    assert "column_info" in item.properties["stac_generator"]
    assert item.properties["stac_generator"]["column_info"] == [
        {"name": "Suburb_Name", "description": "Suburb_Name"}
    ]
    assert "join_config" in item.properties["stac_generator"]
    assert item.properties["stac_generator"]["join_config"]["column_info"] == [
        {"name": "Area", "description": "Area Name"},
        {"name": "Sell_Price", "description": "Median Sales Price in 2025"},
        {"name": "Rent_Price", "description": "Median Rental Price in 2025"},
        {
            "name": "Sell/Rent",
            "description": "Ratio of Sales Price (in $1000) over Rental Price (in $)",
        },
    ]
    assert item.properties["stac_generator"]["join_config"]["file"] == location
    assert item.properties["stac_generator"]["join_config"]["right_on"] == "Area"
    assert item.properties["stac_generator"]["join_config"]["left_on"] == "Suburb_Name"
    assert item.properties["stac_generator"]["join_config"]["date_column"] == "Date"
    assert item.properties["start_datetime"] == start
    assert item.properties["end_datetime"] == end
    assert item.properties["timestamps"] == timestamps


def test_given_invalid_wrong_layer_expects_raises() -> None:
    with pytest.raises(Exception):
        load_items("invalid_wrong_layer.json")


def test_given_invalid_column_info_expects_raises() -> None:
    with pytest.raises(StacConfigException):
        load_items("invalid_column_info.json")


def test_given_no_column_info_expects_no_value_in_property() -> None:
    item = load_item("no_column_info.json")
    assert "column_info" not in item.properties["stac_generator"]


def test_given_column_info_expects_column_info_in_property() -> None:
    item = load_item("with_column_info.json")
    assert "column_info" in item.properties["stac_generator"]
    assert item.properties["stac_generator"]["column_info"] != []


def test_given_with_epsg_expects_epsg_in_property() -> None:
    item = load_item("with_epsg.json")
    assert "proj:code" in item.properties
    assert item.properties["proj:code"] == "EPSG:1168"


def test_given_layers_info_expects_multiple_layers() -> None:
    items = load_items("with_layer.json")
    assert len(items) == 2
    assert items[0].id == "Sunbury"
    assert items[1].id == "Werribee"


def test_given_join_file_invalid_config_left_on_undescribed_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_left_on_undescribed.json")


def test_given_join_file_invalid_no_join_column_info_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_no_join_column_info.json")


def test_given_join_file_invalid_config_no_left_on_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_no_left_on.json")


def test_given_join_file_invalid_config_no_right_on_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_no_right_on.json")


def test_given_join_file_invalid_config_right_on_undescribed_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_right_on_undescribed.json")


def test_given_join_file_invalid_wrong_join_column_info_expects_throw() -> None:
    with pytest.raises(StacConfigException):
        load_item("join_invalid_config_wrong_join_column_info.json")


def test_given_join_file_invalid_wrong_join_date_column_expects_throw() -> None:
    with pytest.raises(StacConfigException):
        load_item("join_invalid_config_wrong_join_date_column.json")


def test_given_join_file_invalid_wrong_left_on_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_wrong_left_on.json")


def test_given_join_file_invalid_wrong_right_on_expects_throw() -> None:
    with pytest.raises(ValueError):
        load_item("join_invalid_config_wrong_right_on.json")


def test_given_join_with_date_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-01T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
        ],
    )


def test_given_join_with_date_custom_tz_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_custom_tz.json")
    # Custom timzone should not affect price since everything is in UTC
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-01T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
        ],
    )


def test_given_join_with_date_no_tzexpects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_no_tz.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price_no_tz.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-01T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
        ],
    )


def test_given_join_with_date_no_tz_utc_timezone_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_no_tz_utc_timezone.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price_no_tz.csv",
        "2020-01-01T11:00:00Z",
        "2025-01-01T11:00:00Z",
        [
            "2020-01-01T11:00:00+00:00",
            "2024-01-01T11:00:00+00:00",
            "2025-01-01T11:00:00+00:00",
        ],
    )


def test_given_join_with_date_multi_tz_local_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_multi_tz_local.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price_multi_tz_multi_area.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-07T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2020-01-02T00:00:00+00:00",
            "2020-01-03T00:00:00+00:00",
            "2020-01-04T00:00:00+00:00",
            "2020-01-05T00:00:00+00:00",
            "2020-01-06T00:00:00+00:00",
            "2020-01-07T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2024-01-02T00:00:00+00:00",
            "2024-01-03T00:00:00+00:00",
            "2024-01-04T00:00:00+00:00",
            "2024-01-05T00:00:00+00:00",
            "2024-01-06T00:00:00+00:00",
            "2024-01-07T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
            "2025-01-02T00:00:00+00:00",
            "2025-01-03T00:00:00+00:00",
            "2025-01-04T00:00:00+00:00",
            "2025-01-05T00:00:00+00:00",
            "2025-01-06T00:00:00+00:00",
            "2025-01-07T00:00:00+00:00",
        ],
    )


def test_given_join_with_date_multi_tz_sydney_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_multi_tz_sydney.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price_multi_tz_multi_area.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-07T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2020-01-02T00:00:00+00:00",
            "2020-01-03T00:00:00+00:00",
            "2020-01-04T00:00:00+00:00",
            "2020-01-05T00:00:00+00:00",
            "2020-01-06T00:00:00+00:00",
            "2020-01-07T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2024-01-02T00:00:00+00:00",
            "2024-01-03T00:00:00+00:00",
            "2024-01-04T00:00:00+00:00",
            "2024-01-05T00:00:00+00:00",
            "2024-01-06T00:00:00+00:00",
            "2024-01-07T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
            "2025-01-02T00:00:00+00:00",
            "2025-01-03T00:00:00+00:00",
            "2025-01-04T00:00:00+00:00",
            "2025-01-05T00:00:00+00:00",
            "2025-01-06T00:00:00+00:00",
            "2025-01-07T00:00:00+00:00",
        ],
    )


# NOTE: this is a very special edge case
# When reading csv using pd.read_csv with parse_dates,
# if a date column has a mixture of tz-awared and non-tz-awared rows,
# the non-tz-awared will be populated with offsets of the nearest tz aware row
def test_given_join_with_date_multi_tz_utc_expects_correct_start_end_datetime() -> None:
    item = load_item("join_with_date_multi_tz_utc.json")
    run_join_with_date_test(
        item,
        "tests/files/unit_tests/vectors/price_multi_tz_multi_area.csv",
        "2020-01-01T00:00:00Z",
        "2025-01-07T00:00:00Z",
        [
            "2020-01-01T00:00:00+00:00",
            "2020-01-02T00:00:00+00:00",
            "2020-01-03T00:00:00+00:00",
            "2020-01-04T00:00:00+00:00",
            "2020-01-05T00:00:00+00:00",
            "2020-01-06T00:00:00+00:00",
            "2020-01-07T00:00:00+00:00",
            "2024-01-01T00:00:00+00:00",
            "2024-01-02T00:00:00+00:00",
            "2024-01-03T00:00:00+00:00",
            "2024-01-04T00:00:00+00:00",
            "2024-01-05T00:00:00+00:00",
            "2024-01-06T00:00:00+00:00",
            "2024-01-07T00:00:00+00:00",
            "2025-01-01T00:00:00+00:00",
            "2025-01-02T00:00:00+00:00",
            "2025-01-03T00:00:00+00:00",
            "2025-01-04T00:00:00+00:00",
            "2025-01-05T00:00:00+00:00",
            "2025-01-06T00:00:00+00:00",
            "2025-01-07T00:00:00+00:00",
        ],
    )


def test_given_join_no_date_expects_same_start_end_datetime() -> None:
    item = load_item("join_no_date.json")
    run_join_nodate_test(
        item,
        "tests/files/unit_tests/vectors/distance.csv",
        "2024-12-31T13:00:00Z",
        "2024-12-31T13:00:00Z",
        ["2024-12-31T13:00:00+00:00"],
    )
    assert pd.Timestamp(item.properties["start_datetime"]) == item.datetime


def test_given_join_no_date_adelaide_expects_same_start_end_datetime() -> None:
    item = load_item("join_no_date_adelaide.json")
    run_join_nodate_test(
        item,
        "tests/files/unit_tests/vectors/distance.csv",
        "2024-12-31T13:30:00Z",
        "2024-12-31T13:30:00Z",
        ["2024-12-31T13:30:00+00:00"],
    )
    assert pd.Timestamp(item.properties["start_datetime"]) == item.datetime


def test_given_join_no_date_melbourne_expects_same_start_end_datetime() -> None:
    item = load_item("join_no_date_melbourne.json")
    run_join_nodate_test(
        item,
        "tests/files/unit_tests/vectors/distance.csv",
        "2024-12-31T13:00:00Z",
        "2024-12-31T13:00:00Z",
        ["2024-12-31T13:00:00+00:00"],
    )
    assert pd.Timestamp(item.properties["start_datetime"]) == item.datetime


def test_given_join_no_date_utc_expects_same_start_end_datetime() -> None:
    item = load_item("join_no_date_utc.json")
    run_join_nodate_test(
        item,
        "tests/files/unit_tests/vectors/distance.csv",
        "2025-01-01T00:00:00Z",
        "2025-01-01T00:00:00Z",
        ["2025-01-01T00:00:00+00:00"],
    )
    assert pd.Timestamp(item.properties["start_datetime"]) == item.datetime
