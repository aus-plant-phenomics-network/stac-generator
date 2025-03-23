from __future__ import annotations

import abc
import json
import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel
from pyproj.crs.crs import CRS

from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.point.schema import _PointConfig
from stac_generator.core.raster.schema import _RasterConfig
from stac_generator.core.vector.schema import _VectorConfig

if TYPE_CHECKING:
    import pystac

logger = logging.getLogger(__name__)


class StacExtensionError(Exception): ...


def get_item_crs(item: pystac.Item) -> CRS:
    """Extract CRS information from item properties.

    This will first look for CRS information encoded as proj extension, in the following order:
    `proj:code, proj:wkt2, proj:projjson, proj:epsg`

    Args:
        item (pystac.Item): stac item

    Raises:
        StacExtensionError: Invalid format for proj:projjson
        StacExtensionError: no crs description available

    Returns:
        CRS: crs of the current item
    """
    if "proj:code" in item.properties:
        return CRS(item.properties.get("proj:code"))
    if "proj:wkt2" in item.properties:
        return CRS(item.properties.get("proj:wkt2"))
    if "proj:projjson" in item.properties:
        try:
            return CRS(json.loads(item.properties.get("proj:projjson")))  # type: ignore[arg-type]
        except json.JSONDecodeError as e:
            raise StacExtensionError("Invalid projjson encoding in STAC config") from e
    if "proj:epsg" in item.properties:
        logger.warning(
            "proj:epsg is deprecated in favor of proj:code. Please consider using proj:code, or if possible, the full wkt2 instead"
        )
        return CRS(int(item.properties.get("proj:epsg")))  # type: ignore[arg-type]
    if "epsg" in item.properties:
        return CRS(int(item.properties.get("epsg")))  # type: ignore[arg-type]
    raise StacExtensionError("Missing CRS information in item properties")


class ParsedConfig(abc.ABC, BaseModel, arbitrary_types_allowed=True):
    id: str
    location: str
    crs: CRS

    @classmethod
    @abc.abstractmethod
    def extract_kwargs(cls, item: pystac.Item, dst: dict[str, Any] | None) -> dict[str, Any]:
        raise NotImplementedError


class ParsedPointConfig(ParsedConfig, _PointConfig):
    @classmethod
    def extract_kwargs(cls, item: pystac.Item, dst: dict[str, Any] | None) -> dict[str, Any]:
        dst = dst if isinstance(dst, dict) else {}
        if "X" not in item.properties:
            raise ValueError(f"Missing X column in properties of item: {item.id}")
        if "Y" not in item.properties:
            raise ValueError(f"Missing Y column in properties of item: {item.id}")
        dst.update(
            {
                "X": item.properties["X"],
                "Y": item.properties["Y"],
                "Z": item.properties.get("Z", None),
                "T": item.properties.get("T", None),
                "date_format": item.properties.get("date_format", "ISO8601"),
                "epsg": item.properties.get("epsg", 4326),
            }
        )
        return dst


class ParsedRasterConfig(ParsedConfig, _RasterConfig):
    @classmethod
    def extract_kwargs(cls, item: pystac.Item, dst: dict[str, Any] | None) -> dict[str, Any]:
        dst = dst if isinstance(dst, dict) else {}
        if "band_info" not in item.properties["band_info"]:
            raise ValueError(f"Missing band_info property for item: {item.id}")
        dst.update({"band_info": item.properties["band_info"]})
        return dst


class ParsedVectorConfig(ParsedConfig, _VectorConfig):
    @classmethod
    def extract_kwargs(cls, item: pystac.Item, dst: dict[str, Any] | None) -> dict[str, Any]:
        dst = dst if isinstance(dst, dict) else {}
        dst.update(
            {
                "layer": item.properties.get("layer", None),
                "join_file": item.properties.get("join_file", None),
                "join_attribute_vector": item.properties.get("join_attribute_vector", None),
                "join_field": item.properties.get("join_field", None),
                "date_format": item.properties.get("date_format", None),
                "join_T_column": item.properties.get("join_T_column", None),
                "join_column_info": item.properties.get("join_column_info", None),
            }
        )
        return dst


EXTENSION_MAP: dict[str, type[ParsedConfig]] = {
    "csv": ParsedPointConfig,
    "txt": ParsedPointConfig,
    "geotiff": ParsedRasterConfig,
    "tiff": ParsedRasterConfig,
    "tif": ParsedRasterConfig,
    "zip": ParsedVectorConfig,
    "geojson": ParsedVectorConfig,
    "json": ParsedVectorConfig,
    "gpkg": ParsedVectorConfig,
    "shp": ParsedVectorConfig,
}


class ConfigParser:
    @classmethod
    def parse_item(cls, item: pystac.Item) -> ParsedConfig:
        if ASSET_KEY not in item.assets:
            raise ValueError(f"Missing asset key {ASSET_KEY} in item: {item.id}")
        item_id = item.id
        location = item.assets[ASSET_KEY].href
        crs = get_item_crs(item)
        extension = location.split(".")[-1]
        if extension in EXTENSION_MAP:
            config_model = EXTENSION_MAP[extension]
            data = config_model.extract_kwargs(
                item, {"id": item_id, "location": location, "crs": crs}
            )
            return config_model(**data)
        raise ValueError(f"Invalid extension: {extension}")
