import datetime
import json

import geopandas as gpd
import httpx
import pystac
import pytest
import pytest_httpx
import shapely
from shapely import Geometry, LineString, MultiLineString, MultiPoint, MultiPolygon, Point, Polygon

from stac_generator.core.base.generator import CollectionGenerator, VectorGenerator
from stac_generator.core.base.utils import (
    force_write_to_stac_api,
    href_is_stac_api_endpoint,
    parse_href,
    read_source_config,
)

VALID_CSV_CONFIG_FILE = "tests/files/unit_tests/configs/csv_config.csv"

VALID_CONFIG_FILES = [
    "tests/files/unit_tests/configs/valid_json_config.json",
    "tests/files/unit_tests/configs/valid_yaml_config.yaml",
    "tests/files/unit_tests/configs/valid_yml_config.yml",
    "tests/files/unit_tests/configs/valid_json_config_one_item.json",
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
        "collection_date": "2017-01-01",
        "collection_time": "00:00:00",
    }
]

INVALID_CONFIG_FILES = [
    # Empty files
    "tests/files/unit_tests/configs/invalid_json_config.json",
    "tests/files/unit_tests/configs/invalid_yaml_config.yaml",
    "tests/files/unit_tests/configs/invalid_yml_config.yml",
    # Invalid file extensions
    "tests/files/unit_tests/configs/invalid_extension_config.ini",
    "tests/files/unit_tests/configs/invalid_extension_config.toml",
    "tests/files/unit_tests/configs/invalid_extension_config.config",
    "tests/files/unit_tests/configs/invalid_extension_config.txt",
]

INVALID_CONFIG_FILES_IDS = [
    "empty_json",
    "empty_yaml",
    "empty_yml",
    "invalid_extension_ini",
    "invalid_extension_toml",
    "invalid_extension_config",
    "invalid_extension_txt",
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
def test_force_write_to_stac_api_given_initial_response_ok_expects_no_resend(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=200, method="POST")
    # Error 500 should be raise if this test fails
    httpx_mock.add_response(status_code=500, method="PUT")
    force_write_to_stac_api("http://localhost:8082", "test_collection", {})


def test_force_write_to_stac_api_given_initial_response_409_expects_send_put_response_given_put_response_ok_expects_no_raise(
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=409, method="POST")
    httpx_mock.add_response(status_code=200, method="PUT")
    force_write_to_stac_api("http://localhost:8082", "test_collection", {})


@pytest.mark.parametrize("code", [400, 401, 403, 404, 405, 500, 501])
def test_force_write_to_stac_api_given_initial_response_4xx_or_5xx_expects_raises(
    code: int,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=code, method="POST")
    with pytest.raises(httpx.HTTPStatusError) as exp_ctx:
        force_write_to_stac_api("http://localhost:8082", "test_collection", {})
    assert exp_ctx.value.response.status_code == code


@pytest.mark.parametrize("code", [400, 401, 403, 404, 405, 500, 501])
def test_force_write_to_stac_api_given_initial_response_409_final_response_expects_4xx_or_5xx_raises(
    code: int,
    httpx_mock: pytest_httpx.HTTPXMock,
) -> None:
    httpx_mock.add_response(status_code=409, method="POST")
    httpx_mock.add_response(status_code=code, method="PUT")
    with pytest.raises(httpx.HTTPStatusError) as exp_ctx:
        force_write_to_stac_api("http://localhost:8082", "test_collection", {})
    assert exp_ctx.value.response.status_code == code


@pytest.mark.parametrize("file_path", INVALID_CONFIG_FILES, ids=INVALID_CONFIG_FILES_IDS)
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


SINGLE_POINT_ITEM = pystac.Item(
    id="point_item",
    geometry=shapely.Point(150.5471916, -24.33986861),
    bbox=[150.5471916, -24.34031206, 150.5505183, -24.33986861],
    datetime=datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
    properties={},
)
SINGLE_POINT_ITEM_NO_START_END_DATETIME = pystac.Item(
    id="point_item",
    geometry=shapely.Point(150.5471916, -24.33986861),
    bbox=[150.5471916, -24.34031206, 150.5505183, -24.33986861],
    datetime=datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
    properties={},
)
MULTIPOINTS_ITEM = pystac.Item(
    id="points_item",
    geometry=shapely.MultiPoint([[150.5571916, -24.34986861], [150.5515183, -24.34131206]]),
    bbox=[150.5515183, -24.34986861, 150.5571916, -24.34131206],
    datetime=datetime.datetime(2017, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
    properties={},
)

EXP_SPATIAL_EXTENT = pystac.SpatialExtent([150.5471916, -24.34986861, 150.5571916, -24.33986861])
EXP_TEMPORAL_EXTENT = pystac.TemporalExtent(
    [
        [
            datetime.datetime(2017, 1, 1, 0, 0, 0, tzinfo=datetime.UTC),
            datetime.datetime(2017, 1, 2, 0, 0, 0, tzinfo=datetime.UTC),
        ]
    ]
)


def test_get_collection_spatial_extent() -> None:
    actual = CollectionGenerator.spatial_extent([SINGLE_POINT_ITEM, MULTIPOINTS_ITEM])
    assert actual.bboxes == EXP_SPATIAL_EXTENT.bboxes


def test_get_collection_temporal_extent() -> None:
    actual = CollectionGenerator.temporal_extent([SINGLE_POINT_ITEM, MULTIPOINTS_ITEM])
    assert actual.intervals == EXP_TEMPORAL_EXTENT.intervals


#######################################################################
# Test geometry method
#######################################################################

GEOMETRY_TEST_SET = {
    "ONE_POINT": (
        gpd.GeoDataFrame(crs="EPSG:4326", data={"geometry": [Point(1, 2)]}),
        Point(1, 2),
    ),
    "MULTIPOINT": (
        gpd.GeoDataFrame(crs="EPSG:4326", data={"geometry": [Point(1, 2), Point(3, 4)]}),
        MultiPoint(((1, 2), (3, 4))),
    ),
    "POINT_AND_MULTIPOINT": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={"geometry": [Point(1, 2), Point(3, 4), MultiPoint(((5, 6), (7, 8)))]},
        ),
        MultiPoint(((1, 2), (3, 4), (5, 6), (7, 8))),
    ),
    "LINESTRING": (
        gpd.GeoDataFrame(crs="EPSG:4326", data={"geometry": [LineString(((1, 2), (3, 4)))]}),
        LineString(((1, 2), (3, 4))),
    ),
    "MULTILINESTRING": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    LineString(((1, 2), (3, 4))),
                    LineString(((5, 6), (7, 8))),
                ]
            },
        ),
        MultiLineString((((1, 2), (3, 4)), ((5, 6), (7, 8)))),
    ),
    "LINESTRING_AND_MULTILINESTRING": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    LineString(((1, 2), (3, 4))),
                    LineString(((5, 6), (7, 8))),
                    MultiLineString(
                        [
                            ((9, 10), (11, 12)),
                            ((13, 14), (15, 16)),
                        ]
                    ),
                ]
            },
        ),
        MultiLineString(
            [
                ((1, 2), (3, 4)),
                ((5, 6), (7, 8)),
                ((9, 10), (11, 12)),
                ((13, 14), (15, 16)),
            ]
        ),
    ),
    "POLYGON": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    Polygon(((1, 2), (3, 4), (5, 6), (1, 2))),
                ]
            },
        ),
        Polygon(((1, 2), (3, 4), (5, 6), (1, 2))),
    ),
    "MULTIPOLYGON": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    Polygon(((1, 2), (3, 4), (5, 6), (1, 2))),
                    Polygon(((7, 8), (9, 10), (11, 12), (7, 8))),
                ]
            },
        ),
        MultiPolygon(
            [
                (((1, 2), (3, 4), (5, 6), (1, 2)), None),
                (((7, 8), (9, 10), (11, 12), (7, 8)), None),
            ]
        ),
    ),
    "POLYGON_AND_MULTIPOLYGON": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    Polygon(((1, 2), (3, 4), (5, 6), (1, 2))),
                    Polygon(((7, 8), (9, 10), (11, 12), (7, 8))),
                    MultiPolygon(
                        [
                            (((13, 14), (15, 16), (17, 18), (13, 14)), None),
                            (((19, 20), (21, 22), (23, 24), (19, 20)), None),
                        ]
                    ),
                ]
            },
        ),
        MultiPolygon(
            [
                (((1, 2), (3, 4), (5, 6), (1, 2)), None),
                (((7, 8), (9, 10), (11, 12), (7, 8)), None),
                (((13, 14), (15, 16), (17, 18), (13, 14)), None),
                (((19, 20), (21, 22), (23, 24), (19, 20)), None),
            ]
        ),
    ),
    "COMPOSITE": (
        gpd.GeoDataFrame(
            crs="EPSG:4326", data={"geometry": [Point(1, 2), LineString(((3, 4), (5, 6)))]}
        ),
        Polygon(((5, 2), (5, 6), (1, 6), (1, 2), (5, 2))),
    ),
    "MORE_THAN_10": (
        gpd.GeoDataFrame(
            crs="EPSG:4326",
            data={
                "geometry": [
                    Point(1, 2),
                    Point(3, 4),
                    Point(5, 6),
                    Point(7, 8),
                    Point(9, 10),
                    Point(11, 12),
                    Point(13, 14),
                    Point(15, 16),
                    Point(17, 18),
                    Point(19, 20),
                    Point(21, 22),
                ]
            },
        ),
        Polygon(((21, 2), (21, 22), (1, 22), (1, 2), (21, 2))),
    ),
}


@pytest.mark.parametrize("df, geom", GEOMETRY_TEST_SET.values(), ids=GEOMETRY_TEST_SET.keys())
def test_geometry(df: gpd.GeoDataFrame, geom: Geometry) -> None:
    actual = VectorGenerator.geometry(df)
    assert actual == geom
