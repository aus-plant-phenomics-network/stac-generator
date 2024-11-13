import json
from typing import Literal, NotRequired, Required

from pydantic import BaseModel, field_validator
from typing_extensions import TypedDict

from stac_generator.base.schema import SourceConfig

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


class ColumnInfo(TypedDict):
    """TypedDict description of Csv columns"""

    name: Required[str]
    """Column name"""
    description: NotRequired[str]
    """Column description"""
    dtype: NotRequired[DTYPE]
    """Column data type"""


class CsvExtension(BaseModel):
    """Csv metadata required for parsing geospatial data from csv source."""

    X: str
    """Column to be treated as longitude/X coordinate"""
    Y: str
    """Column to be treated as latitude/Y coordinate"""
    epsg: int = 4326
    """EPSG code"""
    Z: str | None = None
    """Column to be treated as altitude/Z coordinate"""
    T: str | None = None
    """Column to be treated as time coordinate"""
    column_info: list[str] | list[ColumnInfo] | None = None
    """Description of attributes collected from the csv"""
    date_format: str = "ISO8601"
    """Format to parse dates - will be used if T column is provided"""

    @field_validator("column_info", mode="before")
    @classmethod
    def coerce_to_object(cls, v: str | list[str]) -> list[str] | list[ColumnInfo]:
        """Convert json serialised string of column info into matched object"""
        if isinstance(v, list):
            return v
        parsed = json.loads(v)
        if not isinstance(parsed, list):
            raise ValueError(
                "column_info field expects a json serialisation of a list of ColumnInfo or a list of string"
            )
        return parsed


class CsvConfig(SourceConfig, CsvExtension):
    """Source config exteneded with CsvExtension fields"""
