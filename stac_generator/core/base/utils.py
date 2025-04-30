from __future__ import annotations

import json
import logging
import urllib.parse
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast, overload

import geopandas as gpd
import httpx
import numpy as np
import pandas as pd
import pytz
import yaml
from pyogrio.errors import DataLayerError, DataSourceError
from shapely import Geometry, GeometryCollection, centroid
from timezonefinder import TimezoneFinder

from stac_generator.exceptions import (
    ConfigFormatException,
    InvalidExtensionException,
    SourceAssetException,
    SourceAssetLocationException,
    StacConfigException,
    TimezoneException,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from stac_generator._types import TimeSequence, TimeSeries, Timestamp
    from stac_generator.core.base.schema import ColumnInfo

SUPPORTED_URI_SCHEMES = ["http", "https"]
logger = logging.getLogger(__name__)

TZFinder = TimezoneFinder()


def parse_href(base_url: str, collection_id: str, item_id: str | None = None) -> str:
    """Generate href for collection or item based on id"""
    if item_id:
        return urllib.parse.urljoin(base_url, f"{collection_id}/{item_id}")
    return urllib.parse.urljoin(base_url, f"{collection_id}")


def href_is_stac_api_endpoint(href: str) -> bool:
    """Check if href points to a resource behind a stac api"""
    output = urllib.parse.urlsplit(href)
    return output.scheme in ["http", "https"]


def force_write_to_stac_api(url: str, id: str, json: dict[str, Any]) -> None:
    """Force write a json object to a stac api endpoint."""
    try:
        logger.debug(f"Sending POST request to {url}")
        response = httpx.post(url=url, json=json)
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 409:
            logger.debug(f"Sending PUT request to {url}")
            response = httpx.put(url=f"{url}/{id}", json=json)
            response.raise_for_status()
        else:
            raise err


def read_source_config(href: str) -> list[dict[str, Any]]:
    logger.debug(f"Reading config file from {href}")
    if not href.endswith(("json", "yaml", "yml", "csv")):
        raise InvalidExtensionException(f"Expects one of json, yaml, yml, csv. Received: {href}")
    try:
        if href.endswith(".csv"):
            df = pd.read_csv(href)
            df.replace(np.nan, None, inplace=True)
            return cast(list[dict[str, Any]], df.to_dict("records"))
        if not href.startswith(("http", "https")):
            with Path(href).open("r") as file:
                if href.endswith(("yaml", "yml")):
                    result = yaml.safe_load(file)
                if href.endswith("json"):
                    result = json.load(file)
        else:  # pragma: no cover
            response = httpx.get(href, follow_redirects=True)
            response.raise_for_status()
            if href.endswith("json"):
                result = response.json()
            if href.endswith(("yaml", "yml")):
                result = yaml.safe_load(response.content.decode("utf-8"))
    except Exception as e:
        raise StacConfigException(f"Unable to read config file from {href}") from e

    if isinstance(result, dict):
        return [result]
    if isinstance(result, list):
        return result
    raise ConfigFormatException(
        f"Expects config to be read as a list of dictionary. Provided: {type(result)}"
    )


def calculate_timezone(geometry: Geometry | Sequence[Geometry]) -> str:
    """Calculate timezone from geometry"""
    point = (
        centroid(geometry)
        if isinstance(geometry, Geometry)
        else centroid(GeometryCollection(list(geometry)))
    )
    # Use TimezoneFinder to get the timezone
    timezone_str = TZFinder.timezone_at(lng=point.x, lat=point.y)

    if not timezone_str:
        raise TimezoneException(
            f"Could not determine timezone for coordinates: lon={point.x}, lat={point.y}"
        )  # pragma: no cover
    return timezone_str


def get_timezone(
    timezone: str | Literal["local", "utc"], geometry: Geometry | Sequence[Geometry]
) -> str:
    if timezone == "local":
        return calculate_timezone(geometry)
    return timezone


@overload
def localise_timezone(data: Timestamp, tzinfo: str) -> Timestamp: ...
@overload
def localise_timezone(data: TimeSeries, tzinfo: str) -> TimeSeries: ...


def localise_timezone(data: Timestamp | TimeSeries, tzinfo: str) -> Timestamp | TimeSeries:
    """Add timezone information to data then converts to UTC"""
    try:
        tz = pytz.timezone(tzinfo)
    except Exception as e:
        raise TimezoneException("Invalid timezone localisation") from e

    def localise(row: pd.Timestamp) -> pd.Timestamp:
        if row.tzinfo is None:
            row = row.tz_localize(tz)
        return row.tz_convert(pytz.timezone("UTC"))

    if isinstance(data, pd.Timestamp):
        return localise(data)
    return data.apply(localise)


def _read_csv(
    src_path: str,
    required: set[str] | Sequence[str] | None = None,
    optional: set[str] | Sequence[str] | None = None,
    date_col: str | None = None,
    date_format: str | None = "ISO8601",
    columns: set[str] | set[ColumnInfo] | Sequence[str] | Sequence[ColumnInfo] | None = None,
) -> pd.DataFrame:
    logger.debug(f"Reading csv from path: {src_path}")
    parse_dates: list[str] | bool = [date_col] if isinstance(date_col, str) else False
    usecols: set[str] | None = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if columns:
        usecols = {item["name"] if isinstance(item, dict) else item for item in columns}
        if required:
            usecols.update(required)
        if optional:
            usecols.update(optional)
        if date_col:
            usecols.add(date_col)
    try:
        return pd.read_csv(
            filepath_or_buffer=src_path,
            usecols=list(usecols) if usecols else None,
            date_format=date_format,
            parse_dates=parse_dates,
        )
    except FileNotFoundError as e:
        raise SourceAssetLocationException(e) from None
    except ValueError as e:
        raise StacConfigException(
            f"Unable to read {src_path} using additional configuration parameters"
        ) from e


def is_string_convertible(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Path):
        return value.as_posix()
    raise ValueError(f"Invalid string: {value}")


def read_point_asset(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    epsg: int,
    Z_coord: str | None = None,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    columns: set[str] | set[ColumnInfo] | Sequence[str] | Sequence[ColumnInfo] | None = None,
    timezone: str | Literal["utc", "local"] = "local",
) -> gpd.GeoDataFrame:
    """Read in csv from local disk
    Users must provide at the bare minimum the location of the csv, and the names of the columns to be
    treated as the X and Y coordinates. By default, will read in all columns in the csv. If columns and groupby
    columns are provided, will selectively read specified columns together with the coordinate columns (X, Y, T).
    """
    df = _read_csv(
        src_path=src_path,
        required=[X_coord, Y_coord],
        optional=[Z_coord] if Z_coord else None,
        date_col=T_coord,
        date_format=date_format,
        columns=columns,
    )

    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df[X_coord], df[Y_coord], crs=epsg))
    if T_coord:
        tzinfo = get_timezone(timezone, gdf.geometry)
        gdf[T_coord] = localise_timezone(gdf[T_coord], tzinfo)
    return gdf


def read_vector_asset(
    src_path: str | Path,
    bbox: tuple[float, float, float, float] | None = None,
    columns: set[str] | Sequence[str] | None = None,
    layer: str | int | None = None,
) -> gpd.GeoDataFrame:
    try:
        return gpd.read_file(
            filename=src_path,
            bbox=bbox,
            columns=columns,
            layer=layer,
            engine="pyogrio",  # For predictability
        )
    except DataLayerError:
        raise StacConfigException(f"Invalid layer. File: {src_path}, layer: {layer}") from None
    except DataSourceError as e:
        raise SourceAssetException(e) from None


def read_join_asset(
    src_path: str,
    right_on: str,
    date_format: str,
    date_column: str | None,
    columns: set[str] | Sequence[str] | set[ColumnInfo] | Sequence[ColumnInfo],
    tzinfo: str,
) -> pd.DataFrame:
    df = _read_csv(
        src_path=src_path,
        required=[right_on],
        date_format=date_format,
        date_col=date_column,
        columns=columns,
    )
    if date_column:
        df[date_column] = localise_timezone(df[date_column], tzinfo)
    return df


def add_timestamps(properties: dict[Any, Any], timestamps: TimeSequence) -> None:
    timestamps_str = [item.isoformat(sep="T") for item in timestamps]
    properties["timestamps"] = timestamps_str
