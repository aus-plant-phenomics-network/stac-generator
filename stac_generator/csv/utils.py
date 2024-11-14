import datetime as pydatetime
import json
import logging
from typing import TYPE_CHECKING, Any

import geopandas as gpd
import numpy as np
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely import MultiPoint, Point, to_geojson

from stac_generator._types import TimeExtentT
from stac_generator.csv.schema import ColumnInfo, CsvConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    epsg: int,
    Z_coord: str | None = None,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    columns: list[str] | list[ColumnInfo] | None = None,
) -> gpd.GeoDataFrame:
    """Read in csv from local disk

    Users must provide at the bare minimum the location of the csv, and the names of the columns to be
    treated as the X and Y coordinates. By default, will read in all columns in the csv. If columns and groupby
    columns are provided, will selectively read specified columns together with the coordinate columns (X, Y, T).

    :param src_path: path to csv file
    :type src_path: str
    :param X_coord: name of X field
    :type X_coord: str
    :param Y_coord: name of Y field
    :type Y_coord: str
    :param epsg: epsg code
    :type epsg: int
    :param Z_coord: name of Z field
    :type Z_coord: str
    :param T_coord: name of time field, defaults to None
    :type T_coord: str | None, optional
    :param date_format: format to pass to pandas to parse datetime, defaults to "ISO8601"
    :type date_format: str, optional
    :param columns: band information, defaults to None
    :type columns: list[str] | list[ColumnInfo] | None, optional
    :return: read dataframe
    :rtype: pd.DataFrame
    """
    logger.debug(f"reading csv from path: {src_path}")
    parse_dates: list[str] | bool = [T_coord] if isinstance(T_coord, str) else False
    usecols: list[str] | None = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if columns:
        usecols = [item["name"] if isinstance(item, dict) else item for item in columns]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        if Z_coord:
            usecols.append(Z_coord)
    df = pd.read_csv(
        filepath_or_buffer=src_path,
        usecols=usecols,
        date_format=date_format,
        parse_dates=parse_dates,
    )
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


def calculate_temporal_extent(
    df: gpd.GeoDataFrame | None = None,
    time_col: str | None = None,
    datetime: pydatetime.datetime | None = None,
    start_datetime: pydatetime.datetime | None = None,
    end_datetime: pydatetime.datetime | None = None,
) -> TimeExtentT:
    """Get temporal extent based on Stac specification.

    If the dataframe and time column are provided, the function will obtain the start datetime and end datetime from the dataframe.
    Otherwise use `start_datetime` and `end_datetime` if provided. Otherwise, use `datetime` if provided.


    :param df: Provided dataframe.
    :type df: gpd.GeoDataFrame | None, optional

    :param time_col: Name of time column.
    :type time_col: str | None, optional

    :param datetime: Datetime.
    :type datetime: datetime.datetime | None, optional

    :param start_datetime: Start datetime.
    :type start_datetime: datetime.datetime | None, optional

    :param end_datetime: End datetime.
    :type end_datetime: datetime.datetime | None, optional

    :return: Start datetime, end datetime.
    :rtype: TimeExtentT
    """
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not np.issubdtype(df[time_col].dtype, np.datetime64):
            raise ValueError(
                f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}"
            )
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    if start_datetime and end_datetime:
        return start_datetime, end_datetime
    if datetime:
        return datetime, datetime
    raise ValueError(
        "If datetime is None, both start_datetime and end_datetime values must be provided"
    )


def _calculate_geometry(
    df: gpd.GeoDataFrame,
) -> Point | MultiPoint:
    """Calculate the geometry from geopandas dataframe.

    Work only on point based data

    Returns a `shapely.Point` or `shapely.MultiPoint` depending on the number
    of unique points in the dataframe.

    :param df: source dataframe
    :type df: gpd.GeoDataFrame
    :return: shapely geometry object
    :rtype: Point | MultiPoint
    """
    points: Sequence[Point] = df["geometry"].unique()
    if len(points) == 1:
        return points[0]
    return MultiPoint([[p.x, p.y] for p in points])


def df_to_item(
    df: gpd.GeoDataFrame,
    assets: dict[str, pystac.Asset],
    source_cfg: CsvConfig,
    properties: dict[str, Any],
) -> pystac.Item:
    """Convert geodataframe to pystac Item

    :param df: input dataframe - used for calculating spatial and temporal extent
    :type df: gpd.GeoDataFrame
    :param assets: asset dict - must contain source data with data as key
    :type assets: dict[str, pystac.Asset]
    :param source_cfg: csv config with parsing metadata
    :type source_cfg: CsvConfig
    :param properties: other properties as dict
    :type properties: dict[str, Any]
    :return: generated pystac.Item
    :rtype: pystac.Item
    """
    start_datetime, end_datetime = calculate_temporal_extent(
        df,
        source_cfg.T,
        source_cfg.datetime,
        source_cfg.start_datetime,
        source_cfg.end_datetime,
    )
    geometry = json.loads(to_geojson(_calculate_geometry(df)))
    item = pystac.Item(
        source_cfg.id,
        bbox=df.total_bounds.tolist(),
        geometry=geometry,
        datetime=end_datetime,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        properties=properties,
        assets=assets,
    )
    proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
    proj_ext.apply(epsg=source_cfg.epsg)
    return item
