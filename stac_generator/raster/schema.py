from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field, field_validator, model_validator

from stac_generator.base.schema import SourceConfig

if TYPE_CHECKING:
    import datetime


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


class RasterConfig(SourceConfig):
    """Configuration for raster data sources"""

    epsg: int
    """EPSG code for the raster's coordinate reference system"""
    collection_date: datetime.date
    collection_time: datetime.time
    bands: list[BandInfo]
    """List of band information"""

    @field_validator("bands", mode="before")
    @classmethod
    def parse_bands(cls, v: str) -> list[BandInfo]:
        if isinstance(v, str):
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError("bands parameter expects a json serialisation of a lis of Band")
            return parsed
        raise ValueError(f"Invalid bands dtype: {type(v)}")
