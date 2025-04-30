from __future__ import annotations

from typing import Annotated, Self

from pydantic import BaseModel, BeforeValidator, field_validator, model_validator

from stac_generator.core.base.schema import ColumnInfo, HasColumnInfo, SourceConfig
from stac_generator.core.base.utils import is_string_convertible  # noqa: TCH001


class JoinConfig(BaseModel):
    file: Annotated[str, BeforeValidator(is_string_convertible)]
    left_on: str
    right_on: str
    date_column: str | None = None
    date_format: str = "ISO8601"
    column_info: list[ColumnInfo]

    @field_validator("column_info", mode="after")
    @classmethod
    def check_non_empty_column_info(cls, value: list[ColumnInfo]) -> list[ColumnInfo]:
        if not value:
            raise ValueError("Join file must have non-empty column_info")
        return value


class VectorConfig(SourceConfig, HasColumnInfo):
    """Extended source config with EPSG code."""

    layer: str | None = None
    """Vector layer for multi-layer shapefile"""

    join_config: JoinConfig | None = None
    """Config for join asset if valid"""

    @model_validator(mode="after")
    def check_join_fields_described(self) -> Self:
        if self.join_config:
            vector_columns = {col["name"] for col in self.column_info}
            join_columns = {col["name"] for col in self.join_config.column_info}
            if self.join_config.left_on not in vector_columns:
                raise ValueError("Join field must be described using column_info")
            if self.join_config.right_on not in join_columns:
                raise ValueError("Join field must be described using join file column_info")
        return self
