from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
import json

from pydantic import BaseModel, Field, model_validator
from stac_generator.base.schema import SourceConfig


class BandInfo(BaseModel):
    """Band information for raster data"""

    name: str
    wavelength: Optional[float] = Field(default=None)  # Can be float or None
    nodata: Optional[float] = Field(default=0)  # Default nodata value
    data_type: Optional[str] = Field(default="uint16")  # Default data type for raster band

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
    bands: List[BandInfo]
    """List of band information"""
    transform: Optional[List[float]] = Field(default=None)
    """Affine transform of the raster"""
    shape: Optional[List[int]] = Field(default=None)
    """Shape of the raster as [height, width]"""

    @classmethod
    def parse_fields(cls, data: Any) -> Any:
        """Parse all fields that need preprocessing"""
        if isinstance(data, dict):
            # Parse bands if it's a string
            if isinstance(data.get("bands"), str):
                try:
                    # Remove any single quotes and replace with double quotes for valid JSON
                    bands_str = data["bands"].replace("'", '"')
                    data["bands"] = json.loads(bands_str)
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid bands JSON: {e}")

            # Ensure each band is properly formatted
            if isinstance(data.get("bands"), list):
                processed_bands = []
                for band in data["bands"]:
                    if isinstance(band, str):
                        # Handle case where band might be a string
                        processed_bands.append({"name": band, "wavelength": None})
                    elif isinstance(band, dict):
                        # Keep dictionary format
                        processed_bands.append(band)
                data["bands"] = processed_bands

        return data

    @model_validator(mode="after")
    def set_datetime_from_collection(self) -> RasterSourceConfig:
        """Set datetime fields based on collection date and time"""
        try:
            # Parse the date string
            collection_date = datetime.strptime(self.collection_date, "%Y-%m-%d").date()
            # Parse the time string
            collection_time = datetime.strptime(
                self.collection_time.replace("Z", "+00:00"), "%H:%M:%S%z"
            ).time()

            # Combine date and time
            collection_datetime = datetime.combine(collection_date, collection_time)

            # Set the datetime fields
            self.datetime = collection_datetime
            self.start_datetime = collection_datetime
            self.end_datetime = collection_datetime

        except ValueError as e:
            raise ValueError(f"Error parsing date/time: {e}")

        return self

    class Config:
        arbitrary_types_allowed = True
