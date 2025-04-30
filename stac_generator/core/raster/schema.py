from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator

from stac_generator.core.base.schema import SourceConfig

VALID_COMMON_NAME = Literal[
    "coastal",
    "blue",
    "green",
    "red",
    "rededge",
    "yellow",
    "pan",
    "nir",
    "nir08",
    "nir09",
    "cirrus",
    "swir16",
    "swir22",
    "lwir",
    "lwir11",
    "lwir12",
]


class BandInfo(BaseModel):
    """Band information for raster data"""

    name: Annotated[str, AfterValidator(lambda name: name.lower())]
    common_name: Annotated[
        VALID_COMMON_NAME | None,
        BeforeValidator(
            lambda common_name: common_name.lower() if isinstance(common_name, str) else None
        ),
    ] = None
    wavelength: float | None = None
    nodata: float | None = None
    data_type: str | None = None
    description: str | None = None


class RasterConfig(SourceConfig):
    """Configuration for raster data sources"""

    band_info: list[BandInfo]
    """List of band information - REQUIRED"""
