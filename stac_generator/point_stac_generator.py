# %%
import datetime as pydatetime
from typing import Any, Literal, cast
from uuid import UUID, uuid4
from collections.abc import Sequence
import numpy as np
import pandas as pd
import pystac
from itertools import chain
from stac_generator.types import (
    FrameT,
    BBoxT,
    TimeExtentT,
    DateTimeT,
    GeometryObj,
    PointBandInfo,
    CSVMediaType,
)

# Helper functions


def calculate_spatial_extent(
    df: FrameT,
    X_coord: str,
    Y_coord: str,
) -> BBoxT:
    """Get bounding box from all points in a dataframe based on GeoJSON specification.
    Assume X_coord and Y_coord values are WGS 84 lat lon coordinates.

    Args:
        df (FrameT): input dataframe containing X_coord and Y_coord columns
        X_coord (str): name of X column
        Y_coord (str): name of Y column

    Returns:
        BBoxT: Bounding box coordinate
    """
    min_X, max_X = float(df[X_coord].min()), float(df[X_coord].max())
    min_Y, max_Y = float(df[Y_coord].min()), float(df[Y_coord].max())
    return [[min_X, min_Y], [max_X, max_Y]]


def calculate_temporal_extent(
    df: FrameT | None = None,
    time_col: str | None = None,
    datetime: pydatetime.datetime | None = None,
    start_datetime: pydatetime.datetime | None = None,
    end_datetime: pydatetime.datetime | None = None,
) -> TimeExtentT:
    """Get temporal extent based on STAC specification. Use start_datetime and end_datetime if provided.
    Otherwise use datetime if provided. If the dataframe and time col is provided, will obtain the
    start datetime, end date time from the dataframe. Otherwise get current UTC time.

    Args:
        df (FrameT | None, optional): provided dataframe. Defaults to None.
        time_col (str | None, optional): name of time column. Defaults to None.
        datetime (pydatetime.datetime | None, optional): datetime. Defaults to None.
        start_datetime (pydatetime.datetime | None, optional): start_datetime. Defaults to None.
        end_datetime (pydatetime.datetime | None, optional): end_datetime. Defaults to None.

    Returns:
        TimeExtentT: start datetime, end_datetime
    """
    if start_datetime and end_datetime:
        return start_datetime, end_datetime
    if datetime:
        return None, datetime
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not isinstance(df[time_col].dtype, DateTimeT):
            raise ValueError(
                f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}"
            )
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    else:
        return None, pydatetime.datetime.now(pydatetime.UTC)


def create_collection_name(collection_id: str) -> str:
    if collection_id.lower().endswith("_collection"):
        return collection_id
    if collection_id.endswith("_"):
        return collection_id + "collection"
    return collection_id + "_collection"


def create_item_name(collection_name: str, group_name: str | None = None) -> str:
    suffix = group_name + "_item" if group_name else "item"
    # Collection name is guaranteed to contain collection suffix
    assert collection_name.endswith("collection")
    parts = collection_name.rsplit("collection", 1)
    parts[-1] = suffix
    return "".join(parts)


def calculate_geometry(
    df: FrameT,
    collection_name: str,
    X_coord: str = "X",
    Y_coord: str = "Y",
    item_group: Sequence[str] | None = None,
) -> dict[str, GeometryObj]:
    if not item_group:
        coords = np.unique(df.loc[:, [X_coord, Y_coord]].values, axis=0)
        coord_type: Literal["Point", "MultiPoint"] = "Point" if len(coords) == 1 else "MultiPoint"
        return {create_item_name(collection_name): GeometryObj(type=coord_type, coordinates=coords)}
    unique_df = df.groupby(item_group).apply(  # type: ignore[call-overload]
        lambda group: group[[X_coord, Y_coord]].drop_duplicates()
    )
    geometry_group = {}
    for i in range(len(df)):
        idx = df.index[i]
        group_name = "_".join(chain(*zip(item_group, idx)))
        item_name = create_item_name(collection_name, group_name)
        coords = unique_df.loc[idx]
        coord_type = "Point" if len(coords) == 1 else "MultiPoint"
        geometry_group[item_name] = GeometryObj(type=coord_type, coordinates=coords)
    return geometry_group


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    bands: Sequence[str] | Sequence[PointBandInfo] | None = None,
    item_group: Sequence[str] | None = None,
) -> FrameT:
    parse_dates = [T_coord] if isinstance(T_coord, str) else False
    usecols = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if bands:
        if isinstance(bands[0], str):
            usecols = [item for item in bands]
        else:
            usecols = [item["name"] for item in cast(Sequence[PointBandInfo], bands)]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        # If item group provided -> read in
        if item_group:
            usecols.extend(item_group)
    return pd.read_csv(src_path, parse_dates=parse_dates, date_format=date_format, usecols=usecols)  # type: ignore[call-overload]


def generate_collection(
    # read csv params
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    # Collection metadata information
    collection_id: str | UUID = uuid4(),
    collection_title: str = "Auto-generated collection title",
    collection_description: str = "Auto-generated collection description",
    license: str = "MIT",
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
    # Item and item partition information
    bands: Sequence[str] | Sequence[PointBandInfo] | None = None,
    item_group: Sequence[str] | None = None,
    **kwargs: Any,
) -> pystac.Collection:
    # TODO: license, keyword, other metadata
    # TODO: band information -
    # Asset
    asset = pystac.Asset(
        href=src_path,
        media_type=CSVMediaType,
        description="Raw point dataset as a csv file",
        roles=["data"],
    )

    # Collection name
    collection_name = create_collection_name(str(collection_id))

    # Determine metadata from csv
    df = read_csv(
        src_path=src_path,
        X_coord=X_coord,
        Y_coord=Y_coord,
        T_coord=T_coord,
        date_format=date_format,
        bands=bands,
        item_group=item_group,
    )

    space_bbox = calculate_spatial_extent(df=df, X_coord="X", Y_coord="Y")
    time_bbox = calculate_temporal_extent(
        df=df,
        time_col=T_coord,
        datetime=datetime,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
    geometry_group = calculate_geometry(
        df=df, collection_name=collection_name, X_coord="X", Y_coord="Y", item_group=item_group
    )

    # Construct Item from geometry group
    items = []
    for item_id, geometry in geometry_group.items():
        items.append(
            pystac.Item(
                id=str(item_id),
                geometry=geometry,  # type: ignore[arg-type]
                bbox=space_bbox,  # type: ignore[arg-type]
                datetime=time_bbox[1],
                start_datetime=time_bbox[0],
                end_datetime=time_bbox[1],
                href=src_path,
                assets={"source_file": asset},
                properties={},
            )
        )

    # Construct Collection
    spatial_extent = pystac.SpatialExtent(space_bbox)
    temporal_extent = pystac.TemporalExtent([list(time_bbox)])
    collection = pystac.Collection(
        id=collection_name,
        title=collection_title,
        description=collection_description,
        assets={"source_file": asset},
        extent=pystac.Extent(
            spatial=spatial_extent,
            temporal=temporal_extent,
        ),
    )
    for item in items:
        collection.add_item(item)
    return collection


collection = generate_collection("soilPointDataAllSites_4ML.csv", "Latitude", "Longitude")
# %%
