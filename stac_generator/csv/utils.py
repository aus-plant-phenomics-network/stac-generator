import json
from collections.abc import Sequence
from itertools import chain
from typing import Any, cast

import geopandas as gpd
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely import MultiPoint, Point, to_geojson

from stac_generator.csv.schema import ColumnInfo
from stac_generator.types import DateTimeT, FrameT, PDFrameT, TimeExtentT

__all__ = (
    "calculate_geometry",
    "calculate_temporal_extent",
    "group_df",
    "items_from_group_df",
    "read_csv",
    "to_gdf",
)


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    columns: list[str] | list[ColumnInfo] | None = None,
    groupby: list[str] | None = None,
) -> PDFrameT:
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
    :rtype: PDFrameT
    """
    parse_dates = [T_coord] if isinstance(T_coord, str) else False
    usecols = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if columns:
        if isinstance(columns[0], str):
            usecols = list(columns)
        else:
            usecols = [item["name"] for item in cast(list[ColumnInfo], columns)]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        # If item group provided -> read in
        if groupby:
            usecols.extend(groupby)
    return cast(
        PDFrameT,
        pd.read_csv(src_path, parse_dates=parse_dates, date_format=date_format, usecols=usecols),  # type: ignore[call-overload]
    )


def to_gdf(df: PDFrameT, X_coord: str, Y_coord: str, epsg: int) -> FrameT:
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


def calculate_temporal_extent(
    df: FrameT | None = None,
    time_col: str | None = None,
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
) -> TimeExtentT:
    """Get temporal extent based on Stac specification.

    Use `start_datetime` and `end_datetime` if provided. Otherwise, use `datetime` if provided.
    If the dataframe and time column are provided, the function will obtain the start datetime and end datetime from the dataframe.

    :param df: Provided dataframe.
    :type df: FrameT | None, optional
    :default: None

    :param time_col: Name of time column.
    :type time_col: str | None, optional
    :default: None

    :param datetime: Datetime.
    :type datetime: DateTimeT | None, optional
    :default: None

    :param start_datetime: Start datetime.
    :type start_datetime: DateTimeT | None, optional
    :default: None

    :param end_datetime: End datetime.
    :type end_datetime: DateTimeT | None, optional
    :default: None

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
        if not isinstance(df[time_col].dtype, DateTimeT):
            raise ValueError(
                f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}"
            )
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    raise ValueError(
        "If datetime is None, both start_datetime and end_datetime values must be provided"
    )


def calculate_geometry(
    df: FrameT,
) -> Point | MultiPoint:
    """Calculate the geometry from geopandas dataframe.

    Returns a `shapely.Point` or `shapely.MultiPoint` depending on the number
    of unique points in the dataframe.

    :param df: source dataframe
    :type df: FrameT
    :return: shapely geometry object
    :rtype: Point | MultiPoint
    """
    points: Sequence[Point] = df["geometry"].unique()
    if len(points) == 1:
        return points[0]
    return MultiPoint([[p.x, p.y] for p in points])


def group_df(
    df: FrameT,
    prefix: str,
    groupby: Sequence[str] | None = None,
) -> dict[str, FrameT]:
    """Partition dataframe into sub-dataframes based on fields in `groupby`.
    Each partition will be assigned an item name obtained from the collection name and field values.

    For example, if the collection name is `point_data` and `groupby = ["sites"]` with values being `["A", "B"]`,
    the resulting item names will be `point_data_site_A_item` and `point_data_site_B_item`.

    If `groupby` is not provided, return a single collection item which is the full dataframe.

    :param df: Source dataframe.
    :type df: FrameT

    :param prefix: Prefix for each item ID.
    :type prefix: str

    :param groupby: Fields to partition the dataframe. Must be present in the original dataframe.
    :type groupby: Sequence[str] | None, optional
    :default: None

    :return: Mapping of group name to sub-dataframe.
    :rtype: dict[str, FrameT]
    """
    if not groupby:
        item_name = prefix
        return {item_name: df}
    partition_df = df.groupby(groupby).apply(lambda group: group.drop_duplicates())  # type: ignore[call-overload]
    partition_df = partition_df.reset_index(level=-1, drop=True)
    df_group = {}
    for i in range(len(partition_df)):
        idx = (
            partition_df.index[i] if len(groupby) != 1 else [partition_df.index[i]]
        )  # If groupby has one single item, convert idx to list of 1
        group_name = "_".join([str(item) for item in chain(*zip(groupby, idx, strict=True))])
        item_name = f"{prefix}_{group_name}"
        df_group[item_name] = partition_df.loc[idx, :].reset_index(drop=True)
    return df_group


def items_from_group_df(
    group_df: dict[str, FrameT],
    asset: pystac.Asset,
    epsg: int,
    T: str | None = None,
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
    properties: dict[str, Any] | None = None,
) -> list[pystac.Item]:
    """Extract `shapely.Point` data from partitioned dataframe maps.

    This function takes a group_df - i.e. dictionary of point group name and their
    dataframe (as obtained from `stac_generator.csv.utils.group_df` method) to generate
    a list of pystac.Item based on information from the dataframe.

    :param group_df: dictionary of point group and their source csv
    :type group_df: dict[str, FrameT]
    :param asset: source data asset
    :type asset: pystac.Asset
    :param epsg: epsg code of the source dataframe
    :type epsg: int
    :param T: name of the time column, defaults to None
    :type T: str | None, optional
    :param datetime: pystac datetime metadata, defaults to None
    :type datetime: DateTimeT | None, optional
    :param start_datetime: pystac start_datetime metadata, defaults to None
    :type start_datetime: DateTimeT | None, optional
    :param end_datetime: pystac end_datetime metadata, defaults to None
    :type end_datetime: DateTimeT | None, optional
    :param properties: additional properties to be added to item
    :type properties: dict[str, Any] | None, optional
    :return: list of generated stac items
    :rtype: list[pystac.Item]
    """
    _properties = properties if properties else {}
    assets = {"source": asset}
    items = []
    for item_id, item_df in group_df.items():
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
        items.append(item)
    return items
