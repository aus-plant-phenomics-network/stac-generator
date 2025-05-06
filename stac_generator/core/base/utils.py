from __future__ import annotations

import json
import logging
import re
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

    from pyproj.crs.crs import CRS

    from stac_generator._types import TimeSequence, TimeSeries, Timestamp
    from stac_generator.core.base.schema import ColumnInfo

SUPPORTED_URI_SCHEMES = ["http", "https"]
logger = logging.getLogger(__name__)

TZFinder = TimezoneFinder()


def parse_href(base_url: str, collection_id: str, item_id: str | None = None) -> str:
    """Generate href for collection or item based on id. This is used for generating
    STAC API URL.

    Args:
        base_url (str): base url
        collection_id (str): collection id
        item_id (str | None, optional): item's id. Defaults to None.

    Returns:
        str: built url
    """
    if item_id:
        return urllib.parse.urljoin(base_url, f"{collection_id}/{item_id}")
    return urllib.parse.urljoin(base_url, f"{collection_id}")


def href_is_stac_api_endpoint(href: str) -> bool:
    """Check if href points to a resource behind a stac api

    Args:
        href (str): url

    Returns:
        bool: boolean result
    """
    output = urllib.parse.urlsplit(href)
    return output.scheme in ["http", "https"]


def force_write_to_stac_api(url: str, id: str, json: dict[str, Any]) -> None:
    """Force write a json object to a stac api endpoint.

    Initially try to POST the json. If 409 error encountered, will try a PUT.

    Args:
        url (str): endpoint url
        id (str): collection's id
        json (dict[str, Any]): json body

    Raises:
        err: error encountered other than integrity error
    """
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
    """Read in config from location

    Args:
        href (str): config location

    Raises:
        InvalidExtensionException: if an unrecognised extension is provided. Only accepts json, yaml, yml, csv
        StacConfigException: if the config file cannot be read
        ConfigFormatException: if the config is not a dictionary or a list

    Returns:
        list[dict[str, Any]]: list of raw configs as dictionaries.
    """
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
    """Method to calculate timezone string from a geometry or a sequence of geometries

    If a sequence of geometries is provided, the timezone is provided for the centroid of
    the sequence of geometries.

    Args:
        geometry (Geometry | Sequence[Geometry]): geometry object

    Raises:
        TimezoneException: if timezone cannot be determined from geometry

    Returns:
        str: timezone string
    """
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
    """Get timezone string based on provided timezone option and geometry.

    This invokes the `calculate_timezone` method under the hood if appropriate.

    Args:
        timezone (str | Literal[&quot;local&quot;, &quot;utc&quot;]): timezone parameter from SourceConfig
        geometry (Geometry | Sequence[Geometry]): asset's geometry.

    Returns:
        str: timezone string
    """
    if timezone == "local":
        return calculate_timezone(geometry)
    return timezone


@overload
def localise_timezone(data: Timestamp, tzinfo: str) -> Timestamp: ...
@overload
def localise_timezone(data: TimeSeries, tzinfo: str) -> TimeSeries: ...


def localise_timezone(data: Timestamp | TimeSeries, tzinfo: str) -> Timestamp | TimeSeries:
    """Add timezone information to data then converts to UTC

    Args:
        data (Timestamp | TimeSeries): series of timestamps or a single timestamp
        tzinfo (str): parsed timezone

    Raises:
        TimezoneException: an invalid timezone is provided

    Returns:
        Timestamp | TimeSeries: utc localised timestamp
    """
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
        raise SourceAssetLocationException(str(e) + ". Asset: f{src_path}") from None
    except ValueError as e:
        raise StacConfigException(
            f"Unable to read {src_path} using additional configuration parameters. " + str(e)
        ) from None


def is_string_convertible(value: Any) -> str:
    """Check whether value is string or path

    If value is Path, converts to string via `as_posix`

    Args:
        value (Any): input value

    Raises:
        ValueError: is not a string or Path

    Returns:
        str: string path
    """
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
    """Read in point data from disk or remote

    Users must provide at the bare minimum the location of the csv, and the names of the columns to be
    treated as the X and Y coordinates. By default, will read in all columns in the csv. If columns and groupby
    columns are provided, will selectively read specified columns together with the coordinate columns (X, Y, T).

    Timezone information is used to convert all timestamps to timezone-aware timestamps. Timestamps that are originally
    timezone awared will not be affected. Timestamps that are originally non-timezone awared will be embeded with timezone information.
    Timestamps are subsequently converted to UTC.

    Args:
        src_path (str): source location
        X_coord (str): column to be treated as the x_coordinate
        Y_coord (str): column to be treated as the y coordinate
        epsg (int): epsg code
        Z_coord (str | None, optional): column to be treated as the z coordinate. Defaults to None.
        T_coord (str | None, optional): column to be treated as timestamps. Defaults to None.
        date_format (str, optional): date intepretation method. Defaults to "ISO8601".
        columns (set[str] | set[ColumnInfo] | Sequence[str] | Sequence[ColumnInfo] | None, optional): columns to be read from the point asset. Defaults to None.
        timezone (str | Literal[&quot;utc&quot;, &quot;local&quot;], optional): timezone parameter for embedding non-timezone-aware timestamps. Defaults to "local".

    Returns:
        gpd.GeoDataFrame: read dataframe
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
    """Read in vector asset from disk or remote.

    Users can provide an optional bbox for constraining the region of the vector data to be read, a set
    of columns describing the attributes of interest, and a layer parameter if the asset is a multilayered
    vector asset.

    Args:
        src_path (str | Path): path to asset.
        bbox (tuple[float, float, float, float] | None, optional): bbox to define the region of interest. Defaults to None.
        columns (set[str] | Sequence[str] | None, optional): sequence of columns to be read from the vector file. Defaults to None.
        layer (str | int | None, optional): layer indentifier for a multilayered asset. Defaults to None.

    Raises:
        StacConfigException: if the provided layer is non-existent
        SourceAssetException: if the asset cannot be accessed or is malformatted

    Returns:
        gpd.GeoDataFrame: read dataframe
    """
    try:
        return gpd.read_file(
            filename=src_path,
            bbox=bbox,
            columns=columns,
            layer=layer,
            engine="pyogrio",  # For predictability
        )
    except DataLayerError:
        raise StacConfigException(
            f"Invalid layer. File: {src_path}, layer: {layer}. The config describes a non-existent layer in the vector asset. Fix this error by removing the layer field or changing it to a valid layer."
        ) from None
    except DataSourceError as e:
        raise SourceAssetException(str(e) + f". Asset: {src_path}") from None


def read_join_asset(
    src_path: str,
    right_on: str,
    date_format: str,
    date_column: str | None,
    columns: set[str] | Sequence[str] | set[ColumnInfo] | Sequence[ColumnInfo],
    tzinfo: str,
) -> pd.DataFrame:
    """Read the join asset from disk or remote

    Args:
        src_path (str): path to join asset
        right_on (str): right on attribute from join config
        date_format (str): date format from join config
        date_column (str | None): date column from join config
        columns (set[str] | Sequence[str] | set[ColumnInfo] | Sequence[ColumnInfo]): list of columns to be read in from the asset
        tzinfo (str): timezone information - already parsed using get_timezone

    Returns:
        pd.DataFrame: _description_
    """
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


def extract_epsg(crs: CRS) -> tuple[int, bool]:
    """Extract epsg information from crs object.
    If epsg info can be extracted directly from crs, return that value.
    Otherwise, try to convert the crs info to WKT2 and extract EPSG using regex

    Note that this method may yield unreliable result

    Args:
        crs (CRS): crs object

    Returns:
        tuple[int, bool]: epsg code and reliability flag
    """
    if (result := crs.to_epsg()) is not None:
        return (result, True)
    # Handle WKT1 edge case
    wkt = crs.to_wkt()
    match = re.search(r'ID\["EPSG",(\d+)\]', wkt)
    if match:
        return (int(match.group(1)), True)
    # No match - defaults to 4326

    logger.warning(
        "Cannot determine epsg from vector file. Either provide it in the config or change the source file. Defaults to 4326 but can be incorrect."
    )  # pragma: no cover
    return (4326, False)  # pragma: no cover
