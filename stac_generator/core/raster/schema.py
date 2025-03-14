import json
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from stac_generator.core.base.schema import SourceConfig


class BandInfo(BaseModel):
    """Band information for raster data"""

    name: str
    common_name: str
    wavelength: str | int | float | None = Field(default=None)  # Can be float or None
    nodata: float | None = Field(default=0)  # Default nodata value
    data_type: str | None = Field(default="uint16")  # Default data type for raster band
    description: str | None = Field(default=None)

    @model_validator(mode="before")
    @classmethod
    def check_common_name(cls, data: Any) -> Any:
        # Common name is derived from name if not provided. If provided, ignore
        if (
            isinstance(data, dict)
            and data.get("common_name", None) is None
            and data.get("name", None) is not None
        ):
            data["common_name"] = data["name"]
        return data

    @field_validator("wavelength", mode="before")
    @classmethod
    def parse_wavelength(cls, v: str | float | None) -> float | None:
        if isinstance(v, float) or v is None:
            return v
        if isinstance(v, str) and v == "no band specified":
            return None
        raise ValueError("Invalid wavelength value: {v}")


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
