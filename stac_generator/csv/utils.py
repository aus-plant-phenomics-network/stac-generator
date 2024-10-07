import json
from collections.abc import Sequence
from itertools import chain
from typing import cast

import geopandas as gpd
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely import MultiPoint, Point, to_geojson

from stac_generator.typing import BandInfo, DateTimeT, FrameT, PDFrameT, TimeExtentT


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    bands: list[str] | list[BandInfo] | None = None,
    groupby: list[str] | None = None,
) -> PDFrameT:
    parse_dates = [T_coord] if isinstance(T_coord, str) else False
    usecols = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if bands:
        if isinstance(bands[0], str):
            usecols = list(bands)
        else:
            usecols = [item["name"] for item in cast(list[BandInfo], bands)]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        # If item group provided -> read in
        if groupby:
            usecols.extend(groupby)
    return pd.read_csv(src_path, parse_dates=parse_dates, date_format=date_format, usecols=usecols)  # type: ignore[call-overload]


def to_gdf(df: PDFrameT, X_coord: str, Y_coord: str, epsg: int) -> FrameT:
    return gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))


def calculate_temporal_extent(
    df: FrameT | None = None,
    time_col: str | None = None,
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
) -> TimeExtentT:
    """Get temporal extent based on STAC specification. Use start_datetime and end_datetime if provided.
    Otherwise use datetime if provided. If the dataframe and time col is provided, will obtain the
    start datetime, end date time from the dataframe.

    Args:
        df (FrameT | None, optional): provided dataframe. Defaults to None.
        time_col (str | None, optional): name of time column. Defaults to None.
        datetime (DateTimeT | None, optional): datetime. Defaults to None.
        start_datetime (DateTimeT | None, optional): start_datetime. Defaults to None.
        end_datetime (DateTimeT | None, optional): end_datetime. Defaults to None.

    Returns:
        TimeExtentT: start datetime, end_datetime
    """
    if start_datetime and end_datetime:
        return start_datetime, end_datetime
    if datetime:
        return datetime, datetime
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not isinstance(df[time_col].dtype, DateTimeT):
            raise ValueError(f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}")
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    raise ValueError("If datetime is None, both start_datetime and end_datetime values must be provided")


def calculate_geometry(
    df: FrameT,
) -> Point | MultiPoint:
    points: Sequence[Point] = df["geometry"].unique()
    if len(points) == 1:
        return points[0]
    return MultiPoint([[p.x, p.y] for p in points])


def group_df(
    df: FrameT,
    prefix: str,
    groupby: Sequence[str] | None = None,
) -> dict[str, FrameT]:
    """Partition dataframe into sub-dataframe based on fields in groupby.
    Each partition will be assigned an item name obtained from collection name and field values.

    E.g. If collection name is `point_data` and `groupby = ["sites"]` with values being `["A", "B"]`.
    The resulting item names will be `point_data_site_A_item` and `point_data_site_B_item`.

    If `groupby` is not provided, return a single collection item which is the full dataframe

    Args:
        df (FrameT): source dataframe
        prefix (str): prefix for each item id
        groupby (Sequence[str] | None, optional): fields to partition the df. Must be present in the original df. Defaults to None.

    Returns:
        dict[str, FrameT]: mapping of group name to sub_df
    """
    if not groupby:
        item_name = prefix
        return {item_name: df}
    partition_df = df.groupby(groupby).apply(lambda group: group.drop_duplicates())  # type: ignore[call-overload]
    partition_df = partition_df.reset_index(level=-1, drop=True)
    df_group = {}
    for i in range(len(partition_df)):
        idx = partition_df.index[i] if len(groupby) != 1 else [partition_df.index[i]]  # If groupby has one single item, convert idx to list of 1
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
    bands: list[str] | list[BandInfo] | None = None,
) -> list[pystac.Item]:
    properties = {} if bands is None else {"bands": bands}
    assets = {"source": asset}
    items = []
    for item_id, item_df in group_df.items():
        _start_datetime, _end_datetime = calculate_temporal_extent(item_df, T, datetime, start_datetime, end_datetime)
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
            properties=properties,
            assets=assets,
        )
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.apply(epsg=epsg)
        items.append(item)
    return items
