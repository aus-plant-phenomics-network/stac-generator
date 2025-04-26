from functools import lru_cache
from pathlib import Path

import pandas as pd
import pystac
import pytest

from stac_generator.core.base.utils import read_source_config
from stac_generator.core.point.generator import PointGenerator
from stac_generator.exceptions import StacConfigException, TimezoneException

CONFIG_PATH = Path("tests/files/unit_tests/points/configs")


@lru_cache
def load_item(file: str) -> pystac.Item:
    config_path = CONFIG_PATH / file
    config = read_source_config(str(config_path))
    generator = PointGenerator(config[0])
    return generator.generate()


def test_no_date_expects_start_datetime_end_datetime_same_as_datetime() -> None:
    item = load_item("no_date.json")
    assert item.datetime == pd.Timestamp(item.properties["start_datetime"])
    assert item.datetime == pd.Timestamp(item.properties["end_datetime"])
    assert item.properties["timestamps"] == [pd.Timestamp(item.datetime).isoformat()]


def test_non_default_fields_expects_same_properties() -> None:
    item = load_item("non_default_fields.json")
    assert item.properties["stac_generator"]["description"] == "Non default description"
    assert item.properties["stac_generator"]["license"] == "MIT"


def test_with_altitude_expects_Z_value_in_properties() -> None:
    item = load_item("with_altitude.json")
    assert item.properties["stac_generator"]["Z"] == "elevation"


def test_with_column_info_expects_column_info_in_properties() -> None:
    item = load_item("with_column_info.json")
    assert "column_info" in item.properties["stac_generator"]


def test_no_column_info_expects_no_column_info_in_properties() -> None:
    item = load_item("no_column_info.json")
    assert "column_info" not in item.properties["stac_generator"]


def test_with_date_no_tzinfo_expects_utc_start_end_datetime() -> None:
    item = load_item("with_date_no_tzinfo.json")
    assert item.properties["start_datetime"] == "2022-12-31T13:30:00Z"
    assert item.properties["end_datetime"] == "2023-01-02T13:30:00Z"
    date_range = pd.date_range("2022-12-31T13:30:00Z", "2023-01-02T13:30:00Z")
    exp_ts = [item.isoformat() for item in date_range]
    assert item.properties["timestamps"] == exp_ts


def test_with_date_with_utc_tz_expects_utc_start_end_datetime() -> None:
    item = load_item("with_date_with_utc_tz.json")
    assert item.properties["start_datetime"] == "2023-01-01T00:00:00Z"
    assert item.properties["end_datetime"] == "2023-01-03T00:00:00Z"
    date_range = pd.date_range("2023-01-01T00:00:00Z", "2023-01-03T00:00:00Z")
    exp_ts = [item.isoformat() for item in date_range]
    assert item.properties["timestamps"] == exp_ts


def test_no_date_with_utc_tz_expects_utc_start_end_datetime() -> None:
    item = load_item("no_date_with_utc_tz.json")
    assert item.datetime == pd.Timestamp(item.properties["start_datetime"])
    assert item.properties["start_datetime"] == "2017-01-01T00:00:00Z"
    assert item.properties["end_datetime"] == item.properties["start_datetime"]
    assert item.properties["timestamps"] == [pd.Timestamp(item.datetime).isoformat()]


def test_with_date_with_tzinfo_expects_start_end_datetime() -> None:
    item = load_item("with_date_with_tzinfo.json")
    assert item.properties["start_datetime"] == "2023-01-01T00:00:00Z"
    assert item.properties["end_datetime"] == "2023-01-03T00:00:00Z"
    date_range = pd.date_range("2023-01-01T00:00:00Z", "2023-01-03T00:00:00Z")
    exp_ts = [item.isoformat() for item in date_range]
    assert item.properties["timestamps"] == exp_ts


def test_with_date_with_date_multi_tz_unsorted_utc_expects_start_end_datetime() -> None:
    item = load_item("with_date_multi_tz_unsorted_utc.json")
    assert item.properties["start_datetime"] == "2023-01-01T00:00:00Z"
    assert item.properties["end_datetime"] == "2023-01-03T00:00:00Z"
    date_range = pd.date_range("2023-01-01T00:00:00Z", "2023-01-03T00:00:00Z")
    exp_ts = [item.isoformat() for item in date_range]
    assert item.properties["timestamps"] == exp_ts


def test_with_date_with_date_multi_tz_unsorted_local_expects_start_end_datetime() -> None:
    item = load_item("with_date_multi_tz_unsorted_local.json")
    assert item.properties["start_datetime"] == "2022-12-31T13:30:00Z"
    assert item.properties["end_datetime"] == "2023-01-03T00:00:00Z"
    exp_ts = [
        "2022-12-31T13:30:00+00:00",
        "2023-01-01T00:00:00+00:00",
        "2023-01-01T13:30:00+00:00",
        "2023-01-02T00:00:00+00:00",
        "2023-01-02T13:30:00+00:00",
        "2023-01-03T00:00:00+00:00",
    ]
    assert item.properties["timestamps"] == exp_ts


def test_invalid_altitude_expects_raises() -> None:
    with pytest.raises(StacConfigException):
        load_item("invalid_altitude.json")


def test_invalid_timezone_expects_raises() -> None:
    with pytest.raises(TimezoneException):
        load_item("invalid_tz.json")


def test_invalid_date_expects_raises() -> None:
    with pytest.raises(StacConfigException):
        load_item("invalid_date.json")


def test_invalid_column_info_expects_raises() -> None:
    with pytest.raises(StacConfigException):
        load_item("invalid_column_info.json")
