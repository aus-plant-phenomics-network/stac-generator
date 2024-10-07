import datetime
from typing import Literal

import geopandas as gpd
import pandas as pd
from typing_extensions import TypedDict

DTYPE = Literal[
    "str",
    "int",
    "bool",
    "float",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32",
    "float64",
    "cint16",
    "cint32",
    "cfloat32",
    "cfloat64",
    "other",
]

# Generic Types

NumberT = int | float
DateTimeT = datetime.datetime
TimeExtentT = tuple[DateTimeT | None, DateTimeT | None]  # (start_datetime, end_datetime) format
CSVMediaType = "text/csv"  # https://www.rfc-editor.org/rfc/rfc7111
ExcelMediaType = "application/vnd.ms-excel"  # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
PDFrameT = pd.DataFrame
FrameT = gpd.GeoDataFrame
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
Mode = Literal["append", "overwrite"]


# STAC extension types


class BandInfo(TypedDict):
    """Generic Band Information."""

    name: str
    description: str


class EOBandInfo(BandInfo, total=False):
    """Band Information EO Extension. To be passed as kwargs for
    <a href="https://pystac.readthedocs.io/en/latest/api/extensions/eo.html#pystac.extensions.eo.Band.create">Band.create</a> method

    """

    common_name: str
    center_wavelength: NumberT
    full_width_half_max: NumberT
    solar_illumination: NumberT
