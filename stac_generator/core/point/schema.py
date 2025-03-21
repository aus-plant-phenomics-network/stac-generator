from typing import Any

import pystac

from stac_generator.core.base.schema import HasColumnInfo, ParsedConfig, SourceConfig


class _PointConfig(HasColumnInfo):
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


class PointConfig(SourceConfig, _PointConfig): ...


class ParsedPointConfig(ParsedConfig, _PointConfig):
    @classmethod
    def extract_item(cls, item: pystac.Item) -> dict[str, Any]:
        result = super().extract_item(item)
        if "X" not in item.properties:
            raise ValueError(f"Missing X column in properties of item: {item.id}")
        if "Y" not in item.properties:
            raise ValueError(f"Missing Y column in properties of item: {item.id}")
        result.update(
            {
                "X": item.properties["X"],
                "Y": item.properties["Y"],
                "Z": item.properties.get("Z", None),
                "T": item.properties.get("T", None),
                "date_format": item.properties.get("date_format", "ISO8601"),
                "epsg": item.properties.get("epsg", 4326),
            }
        )
        return result

    @classmethod
    def from_item(cls, item: pystac.Item) -> "ParsedPointConfig":
        return cls.model_validate(cls.extract_item(item))
