import json
from typing import Any, Self

import pystac
from pydantic import field_validator, model_validator

from stac_generator.core.base.schema import ColumnInfo, HasColumnInfo, ParsedConfig, SourceConfig


class _VectorConfig(HasColumnInfo):
    """Extended source config with EPSG code."""

    epsg: int | None = None
    """EPSG code for checking against EPSG code of the vector data"""

    layer: str | None = None
    """Vector layer for multi-layer shapefile"""

    join_file: str | None = None
    """Name of join csv file"""

    join_attribute_vector: str | None = None
    """Attribute of shapefile to join with text file"""

    join_field: str | None = None
    """Field from text file to join with vector file"""

    date_format: str | None = "ISO8601"
    """Date format of text file"""

    join_T_column: str | None = None
    """Time column of text file if any"""

    join_column_info: list[ColumnInfo] | list[str] | None = None
    """List of attributes associated with point/vector data"""

    @field_validator("join_column_info", mode="before")
    @classmethod
    def coerce_to_object_text(
        cls, v: str | list[str] | None
    ) -> list[str] | list[ColumnInfo] | None:
        """Convert json serialised string of column info into matched object"""
        if v is None:
            return None
        if isinstance(v, list):
            return v
        parsed = json.loads(v)
        if not isinstance(parsed, list):
            raise ValueError(
                "column_info field expects a json serialisation of a list of ColumnInfo or a list of string"
            )
        return parsed

    @model_validator(mode="after")
    def validate_join_data(self) -> Self:
        if self.join_file:
            if not self.join_attribute_vector:
                raise ValueError(
                    "join_attribute_vector field is expected when join_file is provided"
                )
            if not self.join_field:
                raise ValueError("join_field is expected when join_file is provided")
            if not self.join_column_info:
                raise ValueError("join_column_info is expected when join_file is provided")
        return self


class VectorConfig(SourceConfig, _VectorConfig): ...


class ParsedVectorConfig(ParsedConfig, _VectorConfig):
    @classmethod
    def extract_item(cls, item: pystac.Item) -> dict[str, Any]:
        result = super().extract_item(item)
        result.update(
            {
                "layer": item.properties.get("layer", None),
                "join_file": item.properties.get("join_file", None),
                "join_attribute_vector": item.properties.get("join_attribute_vector", None),
                "join_field": item.properties.get("join_field", None),
                "date_format": item.properties.get("date_format", None),
                "join_T_column": item.properties.get("join_T_column", None),
                "join_column_info": item.properties.get("join_column_info", None),
            }
        )
        return result

    @classmethod
    def from_item(cls, item: pystac.Item) -> "ParsedVectorConfig":
        return cls.model_validate(cls.extract_item(item))
