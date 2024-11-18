from __future__ import annotations

import json
from datetime import UTC, datetime
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

    @model_validator(mode="after")
    def set_datetime_from_collection(self) -> RasterSourceConfig:
        """Set datetime fields based on collection date and time"""
        try:
            # Parse the date string as timezone-aware
            collection_date = datetime.strptime(self.collection_date, "%Y-%m-%d").replace(
                tzinfo=UTC
            )

            # Handle trailing 'Z' in time string and ensure timezone-awareness
            collection_time_str = self.collection_time.strip()
            if collection_time_str.endswith("Z"):
                collection_time = datetime.strptime(collection_time_str, "%H:%M:%SZ").replace(
                    tzinfo=UTC
                )
            else:
                collection_time = datetime.strptime(collection_time_str, "%H:%M:%S").replace(
                    tzinfo=UTC
                )

            # Combine date and time into a single timezone-aware datetime object
            collection_datetime = datetime.combine(collection_date.date(), collection_time.timetz())

            # Set the datetime fields
            self.datetime = collection_datetime
            self.start_datetime = collection_datetime
            self.end_datetime = collection_datetime

        except ValueError as e:
            raise ValueError(f"Error parsing date/time: {e}") from e

        return self

    class Config:
        arbitrary_types_allowed = True
