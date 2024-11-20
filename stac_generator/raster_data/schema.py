from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, model_validator

from stac_generator.base.schema import SourceConfig


class BandInfo(BaseModel):
    """Band information for raster data"""

    name: str
    wavelength: float | None = Field(default=None)  # Can be float or None
    nodata: float | None = Field(default=0)  # Default nodata value
    data_type: str | None = Field(default="uint16")  # Default data type for raster band

    @model_validator(mode="before")
    @classmethod
    def parse_wavelength(cls, data: Any) -> Any:
        """Handle 'no band specified' case"""
        if isinstance(data, dict) and data.get("wavelength") == "no band specified":
            data["wavelength"] = None
        return data


class RasterSourceConfig(SourceConfig):
    """Configuration for raster data sources"""

    location: str
    """Location of the raster file"""
    epsg: int
    """EPSG code for the raster's coordinate reference system"""
    collection_date: str  # Changed to str to handle the input format
    collection_time: str  # Changed to str to handle the input format
    bands: list[BandInfo]
    """List of band information"""
    transform: list[float] | None = Field(default=None)
    """Affine transform of the raster"""
    shape: list[int] | None = Field(default=None)
    """Shape of the raster as [height, width]"""

    @model_validator(mode="before")
    @classmethod
    def parse_fields(cls, data: Any) -> Any:
        """Parse all fields that need preprocessing"""
        if isinstance(data, dict):
            # Parse bands if it's a string
            if isinstance(data.get("bands"), str):
                try:
                    data["bands"] = json.loads(data["bands"])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid bands JSON: {e}") from e

            # Ensure each band is properly formatted
            if isinstance(data.get("bands"), list):
                data["bands"] = [
                    {"name": band, "wavelength": None} if isinstance(band, str) else band
                    for band in data["bands"]
                ]
        return data
