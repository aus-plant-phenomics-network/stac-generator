import datetime as pydatetime

import geopandas as gpd
import pystac
import pytest
from shapely import Geometry

from stac_generator._types import CsvMediaType
from stac_generator.core.base.generator import VectorGenerator
from stac_generator.core.point.generator import read_csv
from stac_generator.core.point.schema import PointConfig

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
X = "longitude"
Y = "latitude"
Z = "elevation"
T = "YYYY-MM-DD"
EPSG = 7843  # GDA2020
DATE_FORMAT = "ISO8601"
COLLECTION_DATE = pydatetime.date(2011, 1, 1)
COLLECTION_TIME = pydatetime.time(12, 4, 5)

PATHS = {
    "with_date_multi": "tests/files/unit_tests/points/with_date_multi.csv",
    "with_date_one": "tests/files/unit_tests/points/with_date_one.csv",
    "no_date_multi": "tests/files/unit_tests/points/no_date_multi.csv",
    "no_date_one": "tests/files/unit_tests/points/no_date_one.csv",
}
FRAMES = {
    "with_date_multi": read_csv(
        "tests/files/unit_tests/points/with_date_multi.csv", X, Y, EPSG, Z, T, DATE_FORMAT
    ),
    "with_date_one": read_csv(
        "tests/files/unit_tests/points/with_date_one.csv", X, Y, EPSG, Z, T, DATE_FORMAT
    ),
    "no_date_multi": read_csv("tests/files/unit_tests/points/no_date_multi.csv", X, Y, EPSG),
    "no_date_one": read_csv("tests/files/unit_tests/points/no_date_one.csv", X, Y, EPSG),
}
ASSETS = {
    key: pystac.Asset(href=value, roles=["data"], media_type=CsvMediaType)
    for key, value in PATHS.items()
}
CONFIGS = {
    "with_date_multi": PointConfig(
        X=X,
        Y=Y,
        T=T,
        id="test_id",
        location=PATHS["with_date_multi"],
        collection_date=COLLECTION_DATE,
        collection_time=COLLECTION_TIME,
    ),
    "with_date_one": PointConfig(
        X=X,
        Y=Y,
        T=T,
        id="test_id",
        location=PATHS["with_date_one"],
        collection_date=COLLECTION_DATE,
        collection_time=COLLECTION_TIME,
    ),
    "no_date_multi": PointConfig(
        X=X,
        Y=Y,
        id="test_id",
        location=PATHS["no_date_multi"],
        collection_date=COLLECTION_DATE,
        collection_time=COLLECTION_TIME,
    ),
    "no_date_one": PointConfig(
        X=X,
        Y=Y,
        id="test_id",
        location=PATHS["no_date_one"],
        collection_date=COLLECTION_DATE,
        collection_time=COLLECTION_TIME,
    ),
}
GEOMETRIES = {
    "with_date_multi": {
        "type": "MultiPoint",
        "coordinates": [
            [138.5196, -34.9524],
            [138.5296, -34.9624],
            [138.5396, -34.9724],
            [138.5496, -34.9824],
        ],
    },
    "with_date_one": {"type": "Point", "coordinates": [138.5196, -34.9524]},
    "no_date_multi": {
        "type": "MultiPoint",
        "coordinates": [[150.5505183, -24.34031206], [149.8055563, -29.04132741]],
    },
    "no_date_one": {"type": "Point", "coordinates": [150.3125397, -28.18249244]},
}


def test_read_csv_given_no_args_read_all_columns() -> None:
    df = read_csv(PATHS["with_date_one"], X, Y, epsg=EPSG)
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
        PATHS["with_date_one"],
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
    "frame, asset, source_config, geometry",
    zip(FRAMES.values(), ASSETS.values(), CONFIGS.values(), GEOMETRIES.values()),
    ids=FRAMES.keys(),
)
def test_df_to_item(
    frame: gpd.GeoDataFrame,
    asset: pystac.Asset,
    source_config: PointConfig,
    geometry: Geometry,
) -> None:
    item = VectorGenerator.df_to_item(
        df=frame,
        assets={"data": asset},
        source_config=source_config,
        properties={},
        epsg=source_config.epsg,
    )
    assert item.id == source_config.id
    assert item.datetime is not None
    assert item.assets == {"data": asset}
    assert item.geometry == geometry
    assert "proj:code" in item.properties
    assert "proj:wkt2" in item.properties
