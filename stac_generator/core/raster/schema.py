import json
from typing import Any, NotRequired

import pystac
from pydantic import field_validator
from typing_extensions import TypedDict

from stac_generator.core.base.schema import BaseModel, ParsedConfig, SourceConfig


class BandInfo(TypedDict):
    """Band information for raster data"""

    name: str
    common_name: NotRequired[str]
    wavelength: NotRequired[float]
    nodata: NotRequired[float]
    data_type: NotRequired[str]
    description: NotRequired[str]


class _RasterConfig(BaseModel):
    """Configuration for raster data sources"""

    band_info: list[BandInfo]
    """List of band information - REQUIRED"""
    epsg: int | None = None
    """EPSG code for the raster's coordinate reference system"""

    @field_validator("band_info", mode="before")
    @classmethod
    def parse_bands(cls, v: str | list) -> list[BandInfo]:
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("bands parameter expects a json serialisation of a lis of Band")
            return parsed
        raise ValueError(f"Invalid bands dtype: {type(v)}")


class RasterConfig(SourceConfig, _RasterConfig): ...


class ParsedRasterConfig(ParsedConfig, _RasterConfig):
    @classmethod
    def extract_item(cls, item: pystac.Item) -> dict[str, Any]:
        result = super().extract_item(item)
        if "band_info" not in item.properties["band_info"]:
            raise ValueError(f"Missing band_info property for item: {item.id}")
        result.update({"band_info": item.properties["band_info"]})
        return result

    @classmethod
    def from_item(cls, item: pystac.Item) -> "ParsedRasterConfig":
        return cls.model_validate(cls.extract_item(item))
