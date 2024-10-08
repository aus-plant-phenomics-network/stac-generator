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
    name: Required[str]
    """Column name"""
    description: NotRequired[str]
    """Column description"""
    dtype: NotRequired[DTYPE]
    """Column data type"""


class CSVExtension(BaseModel):
    X: str
    Y: str
    epsg: int = 4326
    T: str | None = None
    column_info: list[str] | list[ColumnInfo] | None = None
    groupby: list[str] | None = None
    date_format: str = "ISO8601"

    @field_validator("column_info")
    def coerce_to_object(v: str) -> list[str] | list[ColumnInfo]:
        parsed = json.loads(v)
        if not isinstance(parsed, list):
            raise ValueError("column_info field expects a json serialisation of a list of ColumnInfo or a list of string")
        return parsed


class CSVConfig(SourceConfig, CSVExtension): ...
