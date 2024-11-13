import datetime as pydatetime
import json
from typing import TYPE_CHECKING, Any, cast

import geopandas as gpd
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely import MultiPoint, Point, to_geojson

from stac_generator._types import TimeExtentT
from stac_generator.csv.schema import ColumnInfo

if TYPE_CHECKING:
    from collections.abc import Sequence


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    columns: list[str] | list[ColumnInfo] | None = None,
    groupby: list[str] | None = None,
) -> pd.DataFrame:
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
    :param T_coord: name of time field, defaults to None
    :type T_coord: str | None, optional
    :param date_format: format to pass to pandas to parse datetime, defaults to "ISO8601"
    :type date_format: str, optional
    :param columns: band information, defaults to None
    :type columns: list[str] | list[ColumnInfo] | None, optional
    :param groupby: list of fields that partition the points into groups, defaults to None
    :type groupby: list[str] | None, optional
    :return: read dataframe
    :rtype: pd.DataFrame
    """
    parse_dates: list[str] | bool = [T_coord] if isinstance(T_coord, str) else False
    usecols: list[str] | None = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if columns:
        if isinstance(columns[0], str):
            usecols = cast(list[str], list(columns))
        else:
            usecols = [item["name"] for item in cast(list[ColumnInfo], columns)]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        # If item group provided -> read in
        if groupby:
            usecols.extend(groupby)
    return pd.read_csv(
        filepath_or_buffer=src_path,
        usecols=usecols,
        date_format=date_format,
        parse_dates=parse_dates,
    )


def to_gdf(df: pd.DataFrame, X_coord: str, Y_coord: str, epsg: int) -> gpd.GeoDataFrame:
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


def calculate_temporal_extent(
    df: gpd.GeoDataFrame | None = None,
    time_col: str | None = None,
    datetime: pydatetime.datetime | None = None,
    start_datetime: pydatetime.datetime | None = None,
    end_datetime: pydatetime.datetime | None = None,
) -> TimeExtentT:
    """Get temporal extent based on Stac specification.

    Use `start_datetime` and `end_datetime` if provided. Otherwise, use `datetime` if provided.
    If the dataframe and time column are provided, the function will obtain the start datetime and end datetime from the dataframe.

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
    if start_datetime and end_datetime:
        return start_datetime, end_datetime
    if datetime:
        return datetime, datetime
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not isinstance(df[time_col].dtype, pydatetime.datetime):
            raise ValueError(
                f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}"
            )
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    raise ValueError(
        "If datetime is None, both start_datetime and end_datetime values must be provided"
    )


def calculate_geometry(
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
    item_id: str,
    item_df: gpd.GeoDataFrame,
    asset: pystac.Asset,
    epsg: int,
    T: str | None = None,
    datetime: pydatetime.datetime | None = None,
    start_datetime: pydatetime.datetime | None = None,
    end_datetime: pydatetime.datetime | None = None,
    properties: dict[str, Any] | None = None,
) -> pystac.Item:
    """This function takes a df to generate
    a pystac.Item based on information from the dataframe.

    :param item_id: id of item
    :type item_id: str
    :param item_df: point data in csv
    :type item_df: gpd.GeoDataFrame
    :param asset: source data asset
    :type asset: pystac.Asset
    :param epsg: epsg code of the source dataframe
    :type epsg: int
    :param T: name of the time column, defaults to None
    :type T: str | None, optional
    :param datetime: pystac datetime metadata, defaults to None
    :type datetime: datetime.datetime | None, optional
    :param start_datetime: pystac start_datetime metadata, defaults to None
    :type start_datetime: datetime.datetime | None, optional
    :param end_datetime: pystac end_datetime metadata, defaults to None
    :type end_datetime: datetime.datetime | None, optional
    :param properties: additional properties to be added to item
    :type properties: dict[str, Any] | None, optional
    :return: list of generated stac items
    :rtype: list[pystac.Item]
    """
    _properties = properties if properties else {}
    assets = {"data": asset}
    _start_datetime, _end_datetime = calculate_temporal_extent(
        item_df, T, datetime, start_datetime, end_datetime
    )
    _start_datetime = _start_datetime if _start_datetime is not None else start_datetime
    _end_datetime = _end_datetime if _end_datetime is not None else end_datetime
    _datetime = datetime if datetime else _end_datetime
    _geometry = json.loads(to_geojson(calculate_geometry(item_df)))
    item = pystac.Item(
        item_id,
        bbox=item_df.total_bounds.tolist(),
        geometry=_geometry,
        datetime=_datetime,
        start_datetime=_start_datetime,
        end_datetime=_end_datetime,
        properties=_properties,
        assets=assets,
    )
    proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
    proj_ext.apply(epsg=epsg)
    return item
