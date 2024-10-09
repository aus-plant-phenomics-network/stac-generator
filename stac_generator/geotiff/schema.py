import json
from typing import NotRequired, Required, TypedDict

from pydantic import field_validator

from stac_generator.base.schema import SourceConfig


class EOBandInfo(TypedDict):
    """Arguments to be passed to `eo.bands.create`"""

    name: Required[str]
    common_name: NotRequired[str]
    description: NotRequired[str]
    center_wavelength: NotRequired[float]
    full_width_half_max: NotRequired[float]
    solar_illumination: NotRequired[float]


class GeoTiffConfig(SourceConfig):
    bands: list[EOBandInfo] | None = None

    @field_validator("column_info", mode="before")
    @classmethod
    def coerce_to_object(cls, v: str) -> list[EOBandInfo]:
        """Convert json serialised string of column info into matched object"""
        parsed = json.loads(v)
        if not isinstance(parsed, list):
            raise ValueError(
                "column_info field expects a json serialisation of a list of ColumnInfo or a list of string"
            )
        return parsed
