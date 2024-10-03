from pathlib import Path
from typing import Any, Literal

import pandera as pa
from httpx._types import CookieTypes, HeaderTypes, QueryParamTypes, RequestContent, RequestData
from pydantic import AnyHttpUrl

from stac_generator.typing import DateTimeT, HTTPMethod, Mode


class BaseSchema(pa.DataFrameModel):
    class Config:
        add_missing_columns = True
        coerce = True
        strict = False


class LocationSchema(pa.DataFrameModel):
    """Metadata specifying the file location and how the file location can be accessed. If `local_location` is not provided, raw data is read from `location` using httpx.request parameters (method, params, headers, cookies, content, data, json)"""

    location: AnyHttpUrl
    """URL of the file location. This is under the assumption that the file is hosted somewhere. Primarily used for setting asset's `href`. If the field `local_location` is not provided, will be used as endpoint for fetching data file, using the parameters `method`, `params` and so on."""
    local_location: Path | None = pa.Field(coerce=True)
    """Path to the file on local machine. This is for reading in and processing local file. If local_location is not provided, HTTP methods and other parameters must be provided for reading in the file from `location` field"""
    method: HTTPMethod | None = pa.Field(default="GET")
    """HTTPMethod to acquire the file from location. If method is not provided, the `local_location` value should be specified. If `method` value is not provided, treat as `GET`"""
    params: QueryParamTypes | None = pa.Field(default=None)
    """HTTP query params for getting file from `location`"""
    headers: HeaderTypes | None = pa.Field(default=None)
    """HTTP query headers for getting file from `location`"""
    cookies: CookieTypes | None = pa.Field(default=None)
    """HTTP query cookies for getting file from `location`"""
    content: RequestContent | None = pa.Field(default=None)
    """HTTP query body content for getting file from `location`"""
    data: RequestData | None = pa.Field(default=None)
    """HTTP query body content for getting file from `location`"""
    json: Any | None = pa.Field(default=None)
    """HTTP query body content for getting file from `location`"""


class STACItemMetadataSchema(pa.DataFrameModel):
    datetime: DateTimeT | None = pa.Field(default=None)
    start_datetime: DateTimeT | None = pa.Field(default=None)
    end_datetime: DateTimeT | None = pa.Field(default=None)


class PointSchema(pa.DataFrameModel):
    X: str
    """Name of X coord column in the raw csv file- required - i.e. Longitude or Eastings"""
    Y: str
    """Name of Y coord column in the raw csv file - required i.e. Latitude or Northings"""
    projection: int
    """EPGS projection code - required"""
    T: str | None
    """Name of time coordinate column in the raw csv file - optional"""
    date_format: str | None = pa.Field(default="ISO8601")
    """Date format to interpret `T` column. Accept <a href="https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html">date_format</a> values from `pandas.read_csv` method"""
    group_separator: list[str] | None = pa.Field(default=None, coerce=True)
    """Extra fields inside the source csv that allows the program to split Points into STAC Items. If no `group_separator` is provided, each csv will generate a STAC Item with all included points"""
    bands: list[str]
