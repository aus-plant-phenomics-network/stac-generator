from pathlib import Path

import pandas as pd
import pystac
import pytest

from stac_generator.core.base.utils import read_source_config
from stac_generator.core.point.generator import PointGenerator

CONFIG_PATH = Path("tests/files/unit_tests/points/configs")


def load_item(file: str) -> pystac.Item:
    config_path = CONFIG_PATH / file
    config = read_source_config(str(config_path))
    generator = PointGenerator(config)
    return generator.create_items()[0]


def test_no_date_expects_start_datetime_end_datetime_same_as_datetime() -> None:
    item = load_item("no_date.json")
    assert item.datetime == pd.Timestamp(item.properties["start_datetime"])
    assert item.datetime == pd.Timestamp(item.properties["end_datetime"])


def test_non_default_fields_expects_same_properties() -> None:
    item = load_item("non_default_fields.json")
    assert item.properties["description"] == "Non default description"
    assert item.properties["license"] == "MIT"


def test_with_altitude_expects_Z_value_in_properties() -> None:
    item = load_item("with_altitude.json")
    assert item.properties["Z"] == "elevation"


def test_with_column_info_expects_column_info_in_properties() -> None:
    item = load_item("with_column_info.json")
    assert "column_info" in item.properties


def test_no_column_info_expects_no_column_info_in_properties() -> None:
    item = load_item("no_column_info.json")
    assert "column_info" not in item.properties


def test_with_date_no_tzinfo_expects_utc_start_end_datetime() -> None:
    item = load_item("with_date_no_tzinfo.json")
    assert item.properties["start_datetime"] == "2022-12-31T13:30:00Z"
    assert item.properties["end_datetime"] == "2023-01-02T13:30:00Z"


def test_with_date_with_tzinfo_expects_start_end_datetime() -> None:
    item = load_item("with_date_with_tzinfo.json")
    assert item.properties["start_datetime"] == "2023-01-01T00:00:00Z"
    assert item.properties["end_datetime"] == "2023-01-03T00:00:00Z"


def test_invalid_altitude_expects_raises() -> None:
    with pytest.raises(ValueError):
        load_item("invalid_altitude.json")


def test_invalid_date_expects_raises() -> None:
    with pytest.raises(ValueError):
        load_item("invalid_date.json")


def test_invalid_column_info_expects_raises() -> None:
    with pytest.raises(ValueError):
        load_item("invalid_column_info.json")
