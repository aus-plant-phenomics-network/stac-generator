import json
from typing import NotRequired

from pydantic import field_validator
from typing_extensions import TypedDict

from stac_generator.core.base.schema import SourceConfig


class BandInfo(TypedDict):
    """Band information for raster data"""

    name: str
    common_name: NotRequired[str]
    wavelength: NotRequired[float]
    nodata: NotRequired[float]
    data_type: NotRequired[str]
    description: NotRequired[str]


class RasterConfig(SourceConfig):
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
