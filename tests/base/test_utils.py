import datetime
import json
import urllib.parse

import httpx
import pystac
import pytest
import pytest_httpx
import shapely

from stac_generator.base.utils import (
    extract_spatial_extent,
    extract_temporal_extent,
    force_write_to_stac_api,
    href_is_stac_api_endpoint,
    parse_href,
    read_source_config,
)
from tests import REMOTE_FIXTURE_URL

VALID_CSV_CONFIG_FILE = "tests/files/csv_config.csv"

VALID_CONFIG_FILES = [
    "tests/files/valid_json_config.json",
    "tests/files/valid_yaml_config.yaml",
    "tests/files/valid_yml_config.yml",
]

VALID_NETWORKED_CONFIG_FILES = [
    "unit_tests/config_test/valid_yaml_config.yaml",
    "unit_tests/config_test/valid_json_config.json",
]

CONFIG_OUTPUT = [
    {
        "id": "Grandview",
        "location": "example/csv/Grandview.csv",
        "X": "Longitude",
        "Y": "Latitude",
        "epsg": 4326,
        "column_info": [
            {"name": "Ca_Soln", "description": "Ca concentration"},
            {"name": "pH", "description": "soil pH"},
        ],
    }
]

INVALID_CONFIG_FILES = [
    # Empty files
    "tests/files/invalid_json_config.json",
    "tests/files/invalid_yaml_config.yaml",
    "tests/files/invalid_yml_config.yml",
    # Invalid file extensions
    "tests/files/invalid_extension_config.ini",
    "tests/files/invalid_extension_config.toml",
    "tests/files/invalid_extension_config.cfg",
    "tests/files/invalid_extension_config.txt",
]


@pytest.mark.parametrize(
    "base, collection_id, item_id, exp",
    [
        # Trailing / for base URI should not raise error
        (
            "http://localhost:8082",
            "test_collection",
            "test_item",
            "http://localhost:8082/test_collection/test_item",
        ),
        (
            "http://localhost:8082/",
            "test_collection",
            "test_item",
            "http://localhost:8082/test_collection/test_item",
        ),
        # No item id should not raise error
        (
            "http://localhost:8082/",
            "test_collection",
            None,
            "http://localhost:8082/test_collection",
        ),
    ],
)
def test_parse_href(base: str, collection_id: str, item_id: str | None, exp: str) -> None:
    actual = parse_href(base, collection_id, item_id)
    assert actual == exp


@pytest.mark.parametrize(
    "url, is_local",
    [
        # Href points to a STAC API endpoitn
        ("http://128.4.3.0:8082", False),
        ("https://128.4.3.0", False),
        ("https://somedrive/somepath", False),
        ("http://localhost", False),
        # Href points to a local file or directory
        ("./generated", True),
        ("generated/csv", True),
    ],
)
def test_href_is_stac_api_endpoint(url: str, is_local: bool) -> None:
    actual = href_is_stac_api_endpoint(url)
    assert actual == is_local


@pytest.mark.httpx_mock(assert_all_responses_were_requested=False)
def test_force_write_to_stac_api_given_intial_response_ok_expects_no_resend(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=200, method="POST")
    # Error 500 should be raise if this test fails
    httpx_mock.add_response(status_code=500, method="PUT")
    try:
        force_write_to_stac_api("http://localhost:8082/test_collection", {})
    except Exception:
        raise


def test_force_write_to_stac_api_given_intial_response_409_expects_send_put_response_given_put_response_ok_expects_no_raise(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=409, method="POST")
    httpx_mock.add_response(status_code=200, method="PUT")
    try:
        force_write_to_stac_api("http://localhost:8082/test_collection", {})
    except Exception:
        raise


@pytest.mark.parametrize("code", [400, 401, 403, 404, 405, 500, 501])
def test_force_write_to_stac_api_given_intial_response_4xx_or_5xx_expects_raises(
    code: int,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=code, method="POST")
    with pytest.raises(httpx.HTTPStatusError) as exp_ctx:
        force_write_to_stac_api("http://localhost:8082/test_collection", {})
    assert exp_ctx.value.response.status_code == code


@pytest.mark.parametrize("code", [400, 401, 403, 404, 405, 500, 501])
def test_force_write_to_stac_api_given_intial_response_409_final_response_expects_4xx_or_5xx_raises(
    code: int,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=409, method="POST")
    httpx_mock.add_response(status_code=code, method="PUT")
    with pytest.raises(httpx.HTTPStatusError) as exp_ctx:
        force_write_to_stac_api("http://localhost:8082/test_collection", {})
    assert exp_ctx.value.response.status_code == code


@pytest.mark.parametrize("file_path", INVALID_CONFIG_FILES)
def test_read_source_config_given_invalid_file_expects_raises(file_path: str) -> None:
    with pytest.raises(Exception):
        read_source_config(file_path)


def test_read_source_config_given_valid_csv_file_expects_correct_config_output() -> None:
    actual = read_source_config(VALID_CSV_CONFIG_FILE)
    actual[0]["column_info"] = json.loads(actual[0]["column_info"])
    assert actual == CONFIG_OUTPUT


@pytest.mark.parametrize("href", VALID_CONFIG_FILES)
def test_read_source_config_given_valid_local_files_expects_correct_config_output(
    href: str,
) -> None:
    actual = read_source_config(href)
    assert actual == CONFIG_OUTPUT


@pytest.mark.skipif(
    REMOTE_FIXTURE_URL is None, reason="REMOTE_FIXTURE_URL environment variable unset"
)
@pytest.mark.parametrize("href", VALID_NETWORKED_CONFIG_FILES)
def test_read_source_config_given_valid_remote_files_expects_correct_config_output(
    href: str,
) -> None:
    actual = read_source_config(urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), href))
    assert actual == CONFIG_OUTPUT


SINGLE_POINT_ITEM = pystac.Item(
    id="point_item",
    geometry=shapely.Point(150.5471916, -24.33986861),
    bbox=[150.5471916, -24.34031206, 150.5505183, -24.33986861],
    start_datetime=datetime.datetime(2016, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
    end_datetime=datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
    datetime=datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
    properties={},
)
MULTIPOINTS_ITEM = pystac.Item(
    id="points_item",
    geometry=shapely.MultiPoint([[150.5571916, -24.34986861], [150.5515183, -24.34131206]]),
    bbox=[150.5515183, -24.34986861, 150.5571916, -24.34131206],
    start_datetime=datetime.datetime(2016, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
    end_datetime=datetime.datetime(2017, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
    datetime=datetime.datetime(2017, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
    properties={},
)

EXP_SPATIAL_EXTENT = pystac.SpatialExtent([150.5471916, -24.34986861, 150.5571916, -24.33986861])
EXP_TEMPORAL_EXTENT = pystac.TemporalExtent(
    [
        [
            datetime.datetime(2016, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
            datetime.datetime(2017, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
        ]
    ]
)


def test_extract_spatial_extent() -> None:
    actual = extract_spatial_extent([SINGLE_POINT_ITEM, MULTIPOINTS_ITEM])
    assert actual.bboxes == EXP_SPATIAL_EXTENT.bboxes


def test_extract_temporal_extent() -> None:
    actual = extract_temporal_extent([SINGLE_POINT_ITEM, MULTIPOINTS_ITEM])
    assert actual.intervals == EXP_TEMPORAL_EXTENT.intervals
