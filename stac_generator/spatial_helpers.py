from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

import rasterio
from pyproj import Transformer
from shapely.geometry import Polygon
from shapely.ops import transform


@dataclass
class GeotiffMetadata:
    crs: rasterio.crs.CRS
    bounds: List
    wgs84_bbox: List
    footprint: Polygon
    shape: Tuple[int, int]
    bands_count: int
    dtype: str


def get_metadata_from_geotiff(raster_file) -> GeotiffMetadata:
    with rasterio.open(raster_file) as r:
        bounds = r.bounds
        transformer = Transformer.from_crs(r.crs, "EPSG:4326", always_xy=True)
        footprint = Polygon([[bounds.left, bounds.bottom], [bounds.left, bounds.top], [bounds.right, bounds.top], [bounds.right, bounds.bottom]])
        wgs84_footprint = transform(transformer.transform, footprint)
        wgs84_bounds = wgs84_footprint.bounds
        wgs84_bbox = [wgs84_bounds[0], wgs84_bounds[1], wgs84_bounds[2], wgs84_bounds[3]]
        metadata = GeotiffMetadata(
            crs=r.crs,
            bounds=r.bounds,
            footprint=wgs84_footprint,
            wgs84_bbox=wgs84_bbox,
            shape=(r.height, r.width),
            bands_count=r.count,
            dtype=r.dtypes[0],
        )
    return metadata


class EoBands(Enum):
    """Describes the valid options for common_name of bands in the EO Stac extension."""

    COASTAL = 0.43
    BLUE = 0.47
    GREEN = 0.55
    RED = 0.65
    YELLOW = 0.60
    PAN = 0.60
    REDEDGE = 0.75
    NIR = 0.87
    NIR08 = 0.82
    NIR09 = 0.95
    CIRRUS = 1.37
    SWIR16 = 1.65
    SWIR22 = 2.2
    LWIR = 11.5
    LWIR11 = 11
    LWIR12 = 12
