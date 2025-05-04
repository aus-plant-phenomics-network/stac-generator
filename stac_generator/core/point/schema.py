from __future__ import annotations

from typing import Any

from stac_generator.core.base.schema import HasColumnInfo, SourceConfig


class PointOwnConfig(HasColumnInfo):
    """Source config for point(csv) data"""

    X: str
    """Column to be treated as longitude/X coordinate"""
    Y: str
    """Column to be treated as latitude/Y coordinate"""
    Z: str | None = None
    """Column to be treated as altitude/Z coordinate"""
    T: str | None = None
    """Column to be treated as time coordinate"""
    date_format: str = "ISO8601"
    """Format to parse dates - will be used if T column is provided"""
    epsg: int = 4326
    """EPSG code"""


class PointConfig(SourceConfig, PointOwnConfig):
    def to_asset_config(self) -> dict[str, Any]:
        return PointOwnConfig.model_construct(
            **self.model_dump(mode="json", exclude_none=True, exclude_unset=True)
        ).model_dump(mode="json", exclude_none=True, exclude_unset=True)
