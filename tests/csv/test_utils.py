import datetime as pydatetime
import urllib.parse
from typing import cast

import geopandas as gpd
import pystac
import pytest
from pystac.utils import datetime_to_str

from stac_generator._types import CsvMediaType
from stac_generator.base.generator import VectorGenerator
from stac_generator.csv.generator import read_csv
from stac_generator.csv.schema import CsvConfig
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

SINGLE_POINT_GEOMETRY = {"type": "Point", "coordinates": [-34.9524, 138.5196]}
MULTIPOINT_GEOMETRY = {
    "type": "GeometryCollection",
    "geometries": [
        {"type": "Point", "coordinates": [-34.9524, 138.5196]},
        {"type": "Point", "coordinates": [-34.9624, 138.5296]},
        {"type": "Point", "coordinates": [-34.9724, 138.5396]},
        {"type": "Point", "coordinates": [-34.9824, 138.5496]},
    ],
}

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
    "datetime, start_datetime, end_datetime",
    [
        (None, START_DATE_DUMMY, END_DATE_DUMMY),
        (END_DATE_DUMMY, START_DATE_DUMMY, END_DATE_DUMMY),
        (END_DATE_DUMMY, None, None),
    ],
)
def test_calculate_temporal_extent_given_single_point_with_date_always_return_df_date(
    datetime: pydatetime.datetime | None,
    start_datetime: pydatetime.datetime | None,
    end_datetime: pydatetime.datetime | None,
    single_point_with_date_df: gpd.GeoDataFrame,
) -> None:
    actual = VectorGenerator.temporal_extent(
        single_point_with_date_df, T, datetime, start_datetime, end_datetime
    )
    expected = (
        single_point_with_date_df.loc[:, T].min(),
        single_point_with_date_df.loc[:, T].max(),
    )
    assert actual == expected


@pytest.mark.parametrize(
    "datetime, start_datetime, end_datetime",
    [
        (None, START_DATE_DUMMY, END_DATE_DUMMY),
        (END_DATE_DUMMY, START_DATE_DUMMY, END_DATE_DUMMY),
        (END_DATE_DUMMY, None, None),
    ],
)
def test_calculate_temporal_extent_given_multiple_points_with_date_always_return_df_date(
    datetime: pydatetime.datetime | None,
    start_datetime: pydatetime.datetime | None,
    end_datetime: pydatetime.datetime | None,
    multipoint_with_date_df: gpd.GeoDataFrame,
) -> None:
    actual = VectorGenerator.temporal_extent(
        multipoint_with_date_df, T, datetime, start_datetime, end_datetime
    )
    expected = (
        multipoint_with_date_df.loc[:, T].min(),
        multipoint_with_date_df.loc[:, T].max(),
    )
    assert actual == expected


@pytest.mark.parametrize(
    "datetime, start_datetime, end_datetime, expected",
    [
        (None, START_DATE_DUMMY, END_DATE_DUMMY, (START_DATE_DUMMY, END_DATE_DUMMY)),
        (END_DATE_DUMMY, START_DATE_DUMMY, END_DATE_DUMMY, (START_DATE_DUMMY, END_DATE_DUMMY)),
        (END_DATE_DUMMY, None, None, (END_DATE_DUMMY, END_DATE_DUMMY)),
    ],
)
def test_calculate_temporal_extent_given_single_point_no_date_return_date_arguments(
    datetime: pydatetime.datetime | None,
    start_datetime: pydatetime.datetime | None,
    end_datetime: pydatetime.datetime | None,
    expected: tuple[pydatetime.datetime, pydatetime.datetime],
    single_point_no_date_df: gpd.GeoDataFrame,
) -> None:
    actual = VectorGenerator.temporal_extent(
        single_point_no_date_df, None, datetime, start_datetime, end_datetime
    )
    assert actual == expected


@pytest.mark.parametrize(
    "datetime, start_datetime, end_datetime, expected",
    [
        (None, START_DATE_DUMMY, END_DATE_DUMMY, (START_DATE_DUMMY, END_DATE_DUMMY)),
        (END_DATE_DUMMY, START_DATE_DUMMY, END_DATE_DUMMY, (START_DATE_DUMMY, END_DATE_DUMMY)),
        (END_DATE_DUMMY, None, None, (END_DATE_DUMMY, END_DATE_DUMMY)),
    ],
)
def test_calculate_temporal_extent_given_multipoint_no_date_return_date_arguments(
    datetime: pydatetime.datetime | None,
    start_datetime: pydatetime.datetime | None,
    end_datetime: pydatetime.datetime | None,
    expected: tuple[pydatetime.datetime, pydatetime.datetime],
    multipoint_no_date_df: gpd.GeoDataFrame,
) -> None:
    actual = VectorGenerator.temporal_extent(
        multipoint_no_date_df, None, datetime, start_datetime, end_datetime
    )
    assert actual == expected


@pytest.mark.parametrize(
    "source_cfg, exp_datetime, exp_start_datetime, exp_end_datetime",
    [
        (
            CsvConfig(X=X, Y=Y, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
            END_DATE_DUMMY,
            END_DATE_DUMMY,
            END_DATE_DUMMY,
        ),
        (
            CsvConfig(
                X=X,
                Y=Y,
                id="test_id",
                location="",
                datetime=None,
                start_datetime=START_DATE_DUMMY,
                end_datetime=END_DATE_DUMMY,
                gsd=None,
            ),
            END_DATE_DUMMY,
            START_DATE_DUMMY,
            END_DATE_DUMMY,
        ),
    ],
)
def test_df_to_item_single_point_with_date_given_no_config_date_column_expect_date_from_config(
    source_cfg: CsvConfig,
    exp_datetime: pydatetime.datetime,
    exp_start_datetime: pydatetime.datetime,
    exp_end_datetime: pydatetime.datetime,
    single_point_with_date_df: gpd.GeoDataFrame,
) -> None:
    item = VectorGenerator.df_to_item(
        single_point_with_date_df,
        assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
        source_cfg=source_cfg,
        properties={},
        time_col=source_cfg.T,
        epsg=source_cfg.epsg,
    )
    assert item.id == source_cfg.id
    assert item.datetime == exp_datetime
    assert item.properties["start_datetime"] == datetime_to_str(exp_start_datetime)
    assert item.properties["end_datetime"] == datetime_to_str(exp_end_datetime)
    assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
    assert item.geometry == SINGLE_POINT_GEOMETRY


@pytest.mark.parametrize(
    "source_cfg, exp_datetime, exp_start_datetime, exp_end_datetime",
    [
        (
            CsvConfig(X=X, Y=Y, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
            END_DATE_DUMMY,
            END_DATE_DUMMY,
            END_DATE_DUMMY,
        ),
        (
            CsvConfig(
                X=X,
                Y=Y,
                id="test_id",
                location="",
                datetime=None,
                start_datetime=START_DATE_DUMMY,
                end_datetime=END_DATE_DUMMY,
                gsd=None,
            ),
            END_DATE_DUMMY,
            START_DATE_DUMMY,
            END_DATE_DUMMY,
        ),
    ],
)
def test_df_to_item_single_point_no_date(
    source_cfg: CsvConfig,
    exp_datetime: pydatetime.datetime,
    exp_start_datetime: pydatetime.datetime,
    exp_end_datetime: pydatetime.datetime,
    single_point_no_date_df: gpd.GeoDataFrame,
) -> None:
    item = VectorGenerator.df_to_item(
        single_point_no_date_df,
        assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
        source_cfg=source_cfg,
        properties={},
        time_col=source_cfg.T,
        epsg=source_cfg.epsg,
    )
    assert item.id == source_cfg.id
    assert item.datetime == exp_datetime
    assert item.properties["start_datetime"] == datetime_to_str(exp_start_datetime)
    assert item.properties["end_datetime"] == datetime_to_str(exp_end_datetime)
    assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
    assert item.geometry == SINGLE_POINT_GEOMETRY


@pytest.mark.parametrize(
    "source_cfg",
    [
        CsvConfig(X=X, Y=Y, T=T, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
        CsvConfig(
            X=X,
            Y=Y,
            T=T,
            id="test_id",
            location="",
            datetime=None,
            start_datetime=START_DATE_DUMMY,
            end_datetime=END_DATE_DUMMY,
            gsd=None,
        ),
    ],
)
def test_df_to_item_single_point_given_config_with_date_column_expect_date_from_data(
    source_cfg: CsvConfig,
    single_point_with_date_df: gpd.GeoDataFrame,
) -> None:
    item = VectorGenerator.df_to_item(
        single_point_with_date_df,
        assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
        source_cfg=source_cfg,
        properties={},
        time_col=source_cfg.T,
        epsg=source_cfg.epsg,
    )
    min_date, max_date = VectorGenerator.temporal_extent(single_point_with_date_df, T)
    assert item.id == source_cfg.id
    assert item.datetime == max_date
    assert item.properties["start_datetime"] == datetime_to_str(cast(pydatetime.datetime, min_date))
    assert item.properties["end_datetime"] == datetime_to_str(cast(pydatetime.datetime, max_date))
    assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
    assert item.geometry == SINGLE_POINT_GEOMETRY


@pytest.mark.parametrize(
    "source_cfg",
    [
        CsvConfig(X=X, Y=Y, T=T, id="test_id", location="", datetime=END_DATE_DUMMY, gsd=None),
        CsvConfig(
            X=X,
            Y=Y,
            T=T,
            id="test_id",
            location="",
            datetime=None,
            start_datetime=START_DATE_DUMMY,
            end_datetime=END_DATE_DUMMY,
            gsd=None,
        ),
    ],
)
def test_df_to_item_multipoint_with_date_given_config_with_date_column_expect_date_from_data(
    source_cfg: CsvConfig,
    multipoint_with_date_df: gpd.GeoDataFrame,
) -> None:
    item = VectorGenerator.df_to_item(
        multipoint_with_date_df,
        assets={"data": SINGLE_POINT_WITH_DATE_ASSET},
        source_cfg=source_cfg,
        properties={},
        time_col=source_cfg.T,
        epsg=source_cfg.epsg,
    )
    min_date, max_date = VectorGenerator.temporal_extent(multipoint_with_date_df, T)
    assert item.id == source_cfg.id
    assert item.datetime == max_date
    assert item.properties["start_datetime"] == datetime_to_str(cast(pydatetime.datetime, min_date))
    assert item.properties["end_datetime"] == datetime_to_str(cast(pydatetime.datetime, max_date))
    assert item.assets == {"data": SINGLE_POINT_WITH_DATE_ASSET}
    assert item.geometry == MULTIPOINT_GEOMETRY
