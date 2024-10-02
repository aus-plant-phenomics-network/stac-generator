from typing import Literal, TypedDict
import datetime
import pandas as pd

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
BBoxCoordT = list[NumberT]  # Either 2D or 3D BBoxType
BBoxT = list[BBoxCoordT]  # [[minX, minY], [maxX, maxY]] format for 2D
TimeExtentT = tuple[DateTimeT | None, DateTimeT | None]  # (start_datetime, end_datetime) format
CSVMediaType = "text/csv"  # https://www.rfc-editor.org/rfc/rfc7111
ExcelMediaType = "application/vnd.ms-excel"  # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
FrameT = pd.DataFrame

# GeoJSON types

GeometryT = Literal[
    "Point",
    "MultiPoint",
    "LineString",
    "MultiLineString",
    "Polygon",
    "MultiPolygon",
    "GeometryCollection",
]

Position = tuple[NumberT, NumberT] | tuple[NumberT, NumberT, NumberT]
Point = Position
MultiPoint = list[Position]
LineString = list[Position]
MultiLineString = list[LineString]
LinearRing = list[Position]
Polygon = list[LinearRing]
MultiPolygon = list[Polygon]


class GeometryObj(TypedDict):
    """Python TypedDict object for GeoJSON Geometry Object.

    <a href=https://datatracker.ietf.org/doc/html/rfc7946#section-3.1>Reference</a>

    """

    type: GeometryT
    coordinates: (
        Position | Point | MultiPoint | LineString | MultiLineString | Polygon | MultiPolygon | None
    )


# STAC extension types


class BandInfo(TypedDict):
    """Generic Band Information."""

    name: str


class PointBandInfo(BandInfo, total=False):
    """Band information for point data type."""

    description: str
    dtype: DTYPE


class EOBandInfo(BandInfo, total=False):
    """Band Information EO Extension. To be passed as kwargs for
    <a href="https://pystac.readthedocs.io/en/latest/api/extensions/eo.html#pystac.extensions.eo.Band.create">Band.create</a> method

    """

    description: str
    common_name: str
    center_wavelength: NumberT
    full_width_half_max: NumberT
    solar_illumination: NumberT
