import datetime as pydatetime
import urllib.parse

import geopandas as gpd
import pystac
import pytest
from shapely import Geometry

from stac_generator._types import CsvMediaType
from stac_generator.base.generator import VectorGenerator
from stac_generator.point.generator import read_csv
from stac_generator.point.schema import CsvConfig
from tests import REMOTE_FIXTURE_URL

ALL_COLUMNS = {
    "latitude",
    "longitude",
    "elevation",
    "station",
    "YYYY-MM-DD",
    "daily_rain",
    "max_temp",
    "min_temp",
    "radiation",
    "mslp",
}
X = "latitude"
Y = "longitude"
Z = "elevation"
T = "YYYY-MM-DD"
EPSG = 7843  # GDA2020
DATE_FORMAT = "%Y-%M-%d"

MULTIPOINT_NO_DATE = "unit_tests/point_test/multi_point_no_date.csv"
MULTIPOINT_WITH_DATE = "unit_tests/point_test/multi_point_with_date.csv"
SINGLE_POINT_WITH_DATE = "unit_tests/point_test/single_point_with_date.csv"
SINGLE_POINT_NO_DATE = "unit_tests/point_test/single_point_no_date.csv"

MULTIPOINT_NO_DATE_ASSET = pystac.Asset(
    href=urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), MULTIPOINT_NO_DATE),
    roles=["data"],
    media_type=CsvMediaType,
)
MULTIPOINT_WITH_DATE_ASSET = pystac.Asset(
    href=urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), MULTIPOINT_WITH_DATE),
    roles=["data"],
    media_type=CsvMediaType,
)
SINGLE_POINT_WITH_DATE_ASSET = pystac.Asset(
    href=urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_WITH_DATE),
    roles=["data"],
    media_type=CsvMediaType,
)
SINGLE_POINT_NO_DATE_ASSET = pystac.Asset(
    href=urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_NO_DATE),
    roles=["data"],
    media_type=CsvMediaType,
)

SINGLE_POINT_GEOMETRY = {"type": "Point", "coordinates": [138.5196, -34.9524]}
MULTIPOINT_GEOMETRY = {
    "type": "MultiPoint",
    "coordinates": [
        [138.5196, -34.9524],
        [138.5296, -34.9624],
        [138.5396, -34.9724],
        [138.5496, -34.9824],
    ],
}
COLLECTION_DATE = pydatetime.date(2011, 1, 1)
COLLECTION_TIME = pydatetime.time(12, 4, 5)
START_DATE_DUMMY = pydatetime.datetime(2011, 1, 1, 12, 4, 5, tzinfo=pydatetime.UTC)
END_DATE_DUMMY = pydatetime.datetime(2011, 2, 1, 12, 4, 5, tzinfo=pydatetime.UTC)


@pytest.fixture(scope="module")
def multipoint_with_date_df() -> gpd.GeoDataFrame:
    return read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), MULTIPOINT_WITH_DATE),
        X,
        Y,
        T_coord=T,
        epsg=EPSG,
        date_format=DATE_FORMAT,
    )


@pytest.fixture(scope="module")
def multipoint_no_date_df() -> gpd.GeoDataFrame:
    return read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), MULTIPOINT_NO_DATE), X, Y, epsg=EPSG
    )


@pytest.fixture(scope="module")
def single_point_with_date_df() -> gpd.GeoDataFrame:
    return read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_WITH_DATE),
        X,
        Y,
        epsg=EPSG,
        T_coord=T,
        date_format=DATE_FORMAT,
    )


@pytest.fixture(scope="module")
def single_point_no_date_df() -> gpd.GeoDataFrame:
    return read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_NO_DATE), X, Y, epsg=EPSG
    )


def test_read_csv_given_no_args_read_all_columns() -> None:
    df = read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_WITH_DATE), X, Y, epsg=EPSG
    )
    expected = set(ALL_COLUMNS) | {"geometry"}
    assert set(df.columns) == expected


@pytest.mark.parametrize(
    "z_col, t_col, columns",
    [
        (Z, T, ["max_temp", "min_temp"]),
        (Z, None, ["max_temp", "min_temp"]),
        (None, T, ["max_temp", "min_temp"]),
        (None, None, ["max_temp"]),
    ],
)
def test_read_csv_given_selected_columns_read_selected_columns(
    z_col: str | None,
    t_col: str | None,
    columns: list[str],
) -> None:
    df = read_csv(
        urllib.parse.urljoin(str(REMOTE_FIXTURE_URL), SINGLE_POINT_WITH_DATE),
        X,
        Y,
        epsg=EPSG,
        Z_coord=z_col,
        T_coord=t_col,
        columns=columns,
    )
    expected_columns = {X, Y, "geometry"}
    if z_col is not None:
        expected_columns.add(z_col)
    if t_col is not None:
        expected_columns.add(t_col)
    expected_columns = expected_columns | set(columns)
    assert set(df.columns) == expected_columns


@pytest.mark.parametrize(
    "source_cfg, exp_geometry",
    [
        (
            CsvConfig(
                X=X,
                Y=Y,
                id="test_id",
                location="",
                collection_date=COLLECTION_DATE,
                collection_time=COLLECTION_TIME,
            ),
            SINGLE_POINT_GEOMETRY,
        ),
    ],
)
def test_df_to_item_single_point_no_date(
    source_cfg: CsvConfig,
    exp_geometry: Geometry,
    single_point_no_date_df: gpd.GeoDataFrame,
) -> None:
    item = VectorGenerator.df_to_item(
        single_point_no_date_df,
        assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
        source_cfg=source_cfg,
        properties={},
        epsg=source_cfg.epsg,
    )
    assert item.id == source_cfg.id
    assert item.datetime is not None
    assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
    assert item.geometry == exp_geometry


# @pytest.mark.parametrize(
#     "source_cfg",
#     [
#         CsvConfig(X=X, Y=Y, T=T, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
#         CsvConfig(
#             X=X,
#             Y=Y,
#             T=T,
#             id="test_id",
#             location="",
#             datetime=None,
#             start_datetime=START_DATE_DUMMY,
#             end_datetime=END_DATE_DUMMY,
#             gsd=None,
#         ),
#     ],
# )
# def test_df_to_item_single_point_given_config_with_date_column_expect_date_from_data(
#     source_cfg: CsvConfig,
#     single_point_with_date_df: gpd.GeoDataFrame,
# ) -> None:
#     item = VectorGenerator.df_to_item(
#         single_point_with_date_df,
#         assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
#         source_cfg=source_cfg,
#         properties={},
#         time_col=source_cfg.T,
#         epsg=source_cfg.epsg,
#     )
#     min_date, max_date = VectorGenerator.temporal_extent(single_point_with_date_df, T)
#     assert item.id == source_cfg.id
#     assert item.datetime == max_date
#     assert item.properties["start_datetime"] == datetime_to_str(cast(pydatetime.datetime, min_date))
#     assert item.properties["end_datetime"] == datetime_to_str(cast(pydatetime.datetime, max_date))
#     assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
#     assert item.geometry == SINGLE_POINT_GEOMETRY


# @pytest.mark.parametrize(
#     "source_cfg",
#     [
#         CsvConfig(X=X, Y=Y, T=T, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
#         CsvConfig(
#             X=X,
#             Y=Y,
#             T=T,
#             id="test_id",
#             location="",
#             datetime=None,
#             start_datetime=START_DATE_DUMMY,
#             end_datetime=END_DATE_DUMMY,
#             gsd=None,
#         ),
#     ],
# )
# def test_df_to_item_multipoint_with_date_given_config_with_date_column_expect_date_from_data(
#     source_cfg: CsvConfig,
#     multipoint_with_date_df: gpd.GeoDataFrame,
# ) -> None:
#     item = VectorGenerator.df_to_item(
#         multipoint_with_date_df,
#         assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
#         source_cfg=source_cfg,
#         properties={},
#         time_col=source_cfg.T,
#         epsg=source_cfg.epsg,
#     )
#     min_date, max_date = VectorGenerator.temporal_extent(multipoint_with_date_df, T)
#     assert item.id == source_cfg.id
#     assert item.datetime == max_date
#     assert item.properties["start_datetime"] == datetime_to_str(cast(pydatetime.datetime, min_date))
#     assert item.properties["end_datetime"] == datetime_to_str(cast(pydatetime.datetime, max_date))
#     assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
#     assert item.geometry == MULTIPOINT_GEOMETRY
