from __future__ import annotations

from typing import Annotated, Any, Self

from pydantic import BaseModel, BeforeValidator, field_validator, model_validator

from stac_generator.core.base.schema import ColumnInfo, HasColumnInfo, SourceConfig
from stac_generator.core.base.utils import is_string_convertible  # noqa: TCH001


class VectorOwnConfig(HasColumnInfo):
    """Config that defines the minimum information for parsing and reading vector asset.
    This config is produced for vector asset when the method `to_asset_config` is invoked,
    or when `StacGeneratorFactory.extract_item_config` is called on a vector STAC Item.
    """

    layer: str | None = None
    """Vector layer for multi-layer shapefile."""

    join_config: JoinConfig | None = None
    """Config for join asset if valid available."""

    @model_validator(mode="after")
    def check_join_fields_described(self) -> Self:
        """Validates that if join config is provided, the field `left_on` must be described by the vector's `column_info`. Also
        validates that `right_on` must be described by the join config's `column_info`.
        """
        if self.join_config:
            vector_columns = {col["name"] for col in self.column_info}
            join_columns = {col["name"] for col in self.join_config.column_info}
            if self.join_config.left_on not in vector_columns:
                raise ValueError("Join field must be described using column_info")
            if self.join_config.right_on not in join_columns:
                raise ValueError("Join field must be described using join file column_info")
        return self


class VectorConfig(SourceConfig, VectorOwnConfig):
    """Extends SourceConfig to describe vector asset."""

    def to_asset_config(self) -> dict[str, Any]:
        """Produce a dictionary that has the signature of `VectorOwnConfig`"""
        return VectorOwnConfig.model_construct(
            **self.model_dump(mode="json", exclude_none=True, exclude_unset=True)
        ).model_dump(mode="json", exclude_none=True, exclude_unset=True, warnings=False)


class JoinConfig(BaseModel):
    """Schema for join asset. This also contains information on how the vector asset and the join asset should be merged.

    Merge terminologies are consistent with <a href="https://pandas.pydata.org/docs/reference/api/pandas.merge.html">pandas'</a>, where
    the vector asset is treated as the left table, and the join asset is the right table.
    """

    file: Annotated[str, BeforeValidator(is_string_convertible)]
    """Path to asset. Must be a string or a Path."""
    left_on: str
    """Vector asset's attribute for joining."""
    right_on: str
    """Join asset's attribute for joining."""
    date_column: str | None = None
    """Name of the attribute in the join asset to be treated as timestamps."""
    date_format: str = "ISO8601"
    """Format for intepreting timestamps. Accepted values follows <a href="https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes">strptime/strftime</a> formats."""
    column_info: list[ColumnInfo]
    """List of join asset column attribute. Note that for join assset, this cannot be empty."""

    @field_validator("column_info", mode="after")
    @classmethod
    def check_non_empty_column_info(cls, value: list[ColumnInfo]) -> list[ColumnInfo]:
        """Method to validate that column info is non empty"""
        if not value:
            raise ValueError("Join file must have non-empty column_info")
        return value
