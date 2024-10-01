import datetime as pydatetime
from collections.abc import Sequence
from typing import Any, Literal, TypedDict, cast
from uuid import UUID, uuid4

import numpy as np
import pandas as pd
import pystac
from pyproj import CRS, Transformer

NumberT = int | float
DateTimeT = pydatetime.datetime
CoordT = Literal["latlon", "utm"]
BBoxCoordT = tuple[NumberT, NumberT] | tuple[NumberT, NumberT, NumberT]  # Either 2D or 3D BBoxType
BBoxT = tuple[BBoxCoordT, BBoxCoordT]
TimeExtentT = tuple[DateTimeT | None, DateTimeT | None]
CSVMediaType = "text/csv"  # https://www.rfc-editor.org/rfc/rfc7111
ExcelMediaType = "application/vnd.ms-excel"  # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
FrameT = pd.DataFrame

# TODO: Band extension?
# TODO: MultiPoint vs GeometryCollection of Points

GeometryT = Literal["Point", "MultiPoint", "LineString", "MultiLineString", "Polygon", "MultiPolygon", "GeometryCollection"]


class GeometryObj(TypedDict):
    type: GeometryT
    coordinates: Sequence


def convert_coord_to_latlon(
    df: FrameT,
    X_coord: str,
    Y_coord: str,
    coord_type: CoordT,
    projection: str = "EPSG:4326",
    zone: int | None = None,
    south: bool | None = None,
) -> FrameT:
    if coord_type.lower() == "latlon":
        df["X"], df["Y"] = df[X_coord], df[Y_coord]
    elif coord_type.lower() == "utm":
        if "zone" is None or "south" is None:
            raise ValueError("UTM zone coordinates require utm zone and south information")
        crs = CRS.from_dict({"proj": "utm", "zone": zone, "south": south})
        transformer = Transformer.from_crs(crs_from=crs, crs_to=CRS.from_string(projection))
        values = transformer.transform(df[X_coord].values, df[Y_coord].values)
        df["X"], df["Y"] = values
    else:
        raise ValueError(f"Acceptable coordinate type - latlon, utm. Provided: {coord_type}")
    return df


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
    return ((min_X, min_Y), (max_X, max_Y))


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
        return datetime, None
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not isinstance(df[time_col].dtype, DateTimeT):
            raise ValueError(f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}")
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    else:
        return pydatetime.datetime.now(pydatetime.UTC), None


def calculate_geometry(df: FrameT, X_coord: str = "X", Y_coord: str = "Y") -> GeometryObj:
    coords = np.unique(df.loc[:, [X_coord, Y_coord]].values, axis=0)
    return GeometryObj(type="MultiPoint", coordinates=coords)


def read_csv(
    src_path: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
) -> FrameT:
    parse_dates = [T_coord] if isinstance(T_coord, str) else False
    return pd.read_csv(src_path, parse_dates=parse_dates, date_format=date_format)  # type: ignore[call-overload]


def generate_collection(
    src_path: str,
    collection_description: str,
    collection_title: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    coord_type: CoordT = "latlon",
    zone: int | None = None,
    south: bool = True,
    projection: str = "EPSG:4326",
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
    item_id: str | UUID = uuid4(),
    collection_id: str | UUID = uuid4(),
    **kwargs: Any,
) -> pystac.Collection:
    # Asset
    asset = pystac.Asset(href=src_path, media_type=CSVMediaType, description="Raw point dataset as a csv file", roles=["data"])

    # Determine metadata from csv
    df = read_csv(src_path=src_path, T_coord=T_coord, date_format=date_format, **kwargs)
    df = convert_coord_to_latlon(
        df=df,
        X_coord=X_coord,
        Y_coord=Y_coord,
        coord_type=coord_type,
        projection=projection,
        zone=zone,
        south=south,
    )

    space_bbox = calculate_spatial_extent(df=df, X_coord="X", Y_coord="Y")
    time_bbox = calculate_temporal_extent(
        df=df,
        time_col=T_coord,
        datetime=datetime,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
    )
    geometry = calculate_geometry(df=df, X_coord="X", Y_coord="Y")

    # Construct Item and Catalog
    item = pystac.Item(
        id=str(item_id),
        geometry=geometry,  # type: ignore[arg-type]
        bbox=space_bbox,  # type: ignore[arg-type]
        datetime=datetime,
        start_datetime=start_datetime,
        end_datetime=end_datetime,
        href=src_path,
        assets={"source_file": asset},
        properties={},
    )
    spatial_extent = pystac.SpatialExtent(cast(list[NumberT], space_bbox))
    temporal_extent = pystac.TemporalExtent([list(time_bbox)])
    collection = pystac.Collection(
        id=str(collection_id),
        title=collection_title,
        description=collection_description,
        extent=pystac.Extent(
            spatial=spatial_extent,
            temporal=temporal_extent,
        ),
    )
    collection.add_item(item)
    return collection
