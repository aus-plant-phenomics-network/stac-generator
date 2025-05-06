from __future__ import annotations

from typing import Annotated, Any, Literal

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


class RasterOwnConfig(BaseModel):
    """Config that defines the minimum information for parsing and reading raster asset. This config is produced for raster asset when the method `to_asset_config` is invoked, or when `StacGeneratorFactory.extract_item_config` is called on a raster STAC Item."""

    band_info: list[BandInfo]
    """List of band information - REQUIRED"""


class RasterConfig(SourceConfig, RasterOwnConfig):
    """Extends SourceConfig to describe raster asset."""

    def to_asset_config(self) -> dict[str, Any]:
        """Produce a dictionary that has the signature of `RasterOwnConfig`"""
        return RasterOwnConfig.model_construct(
            **self.model_dump(mode="json", exclude_none=True, exclude_unset=True)
        ).model_dump(mode="json", exclude_none=True, exclude_unset=True, warnings=False)


class BandInfo(BaseModel):
    """Band information for raster data"""

    name: Annotated[str, AfterValidator(lambda name: name.lower())]
    """Band name. Will be converted to lower case for serialisation"""
    common_name: Annotated[
        VALID_COMMON_NAME | None,
        BeforeValidator(
            lambda common_name: common_name.lower() if isinstance(common_name, str) else None
        ),
    ] = None
    """Band's common name. Users should only provide one of the <a href="https://github.com/stac-extensions/eo/blob/main/README.md#common-band-names">supported</a> names."""
    wavelength: float | None = None
    """Band's wavelength"""
    nodata: float | None = None
    """Band's nodata value"""
    data_type: str | None = None
    """Band's data_type"""
    description: str | None = None
    """Band's description"""
