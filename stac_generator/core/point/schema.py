from __future__ import annotations

from stac_generator.core.base.schema import HasColumnInfo, SourceConfig


class PointConfig(SourceConfig, HasColumnInfo):
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
