from __future__ import annotations

import json
from typing import cast

import pystac
import rasterio
from pyproj import CRS
from pyproj.transformer import Transformer
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.projection import AssetProjectionExtension, ItemProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
from shapely import box, to_geojson

from stac_generator.core.base.generator import ItemGenerator
from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.base.utils import add_timestamps
from stac_generator.exceptions import SourceAssetException

from .schema import RasterConfig

VALID_COMMON_NAME = {
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
}


class RasterGenerator(ItemGenerator[RasterConfig]):
    """Raster Generator"""

    def generate(self) -> pystac.Item:
        """Generate Raster Item from config

        :param self.config: raster config - must contain band info
        :type self.config: RasterConfig
        :raises ValueError: if epsg code is provided in config but does not match that extracted from the asset
        :return: generated item
        :rtype: pystac.Item
        """
        try:
            with rasterio.open(self.config.location) as src:
                bounds = src.bounds
                crs = cast(CRS, src.crs)
                shape = list(src.shape)
        except rasterio.errors.RasterioIOError as e:
            raise SourceAssetException("Unable to read raster asset") from e

        # Convert to 4326 for bbox and geometry
        transformer = Transformer.from_crs(crs, 4326, always_xy=True)
        minx, miny = transformer.transform(bounds.left, bounds.bottom)
        maxx, maxy = transformer.transform(bounds.right, bounds.top)
        bbox: tuple[float, float, float, float] = (minx, miny, maxx, maxy)

        # Create geometry as Shapely Polygon
        geometry = box(*bbox)
        geometry_geojson = json.loads(to_geojson(geometry))

        # Process datetime
        item_ts = self.config.get_datetime(geometry)

        # Get EPSG
        epsg = crs.to_epsg()

        # Create STAC Item
        # Start datetime and end_datetime are set to be collection datetime for Raster data
        properties = {
            "stac_generator": self.config.to_properties(),
        }
        add_timestamps(properties, [item_ts])
        item = pystac.Item(
            id=self.config.id,
            geometry=geometry_geojson,
            bbox=list(bbox),
            datetime=item_ts,
            properties=properties,
            start_datetime=item_ts,
            end_datetime=item_ts,
        )

        # Projection extension
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        affine_transform = [
            rasterio.transform.from_bounds(*bounds, shape[1], shape[0])[i] for i in range(9)
        ]
        proj_ext.apply(epsg=epsg, wkt2=crs.to_wkt(), shape=shape, transform=affine_transform)

        # Create EO and Raster bands
        eo_bands = []
        raster_bands = []

        for band_info in self.config.band_info:
            common_name = band_info.get("common_name", None)
            if common_name and common_name not in VALID_COMMON_NAME:
                raise ValueError(f"Invalid common name: {common_name} for item: {self.config.id}")
            eo_band = Band.create(
                name=band_info["name"],
                common_name=common_name,
                center_wavelength=band_info.get("wavelength", None),
                description=band_info.get("description", None),
            )
            eo_bands.append(eo_band)

            raster_band = RasterBand.create(
                nodata=band_info.get("nodata", 0),
                data_type=DataType(band_info.get("data_type"))
                if band_info.get("data_type", None)
                else None,
            )
            raster_bands.append(raster_band)

        # Create Asset and Add to Item
        asset = pystac.Asset(
            href=self.config.location,
            media_type=pystac.MediaType.GEOTIFF,
            roles=["data"],
            title="Raster Data",
        )
        item.add_asset(ASSET_KEY, asset)

        # Apply projection extension to asset
        asset_proj_ext = AssetProjectionExtension.ext(asset, add_if_missing=True)
        asset_proj_ext.apply(
            epsg=crs.to_epsg(), wkt2=crs.to_wkt(), shape=shape, transform=affine_transform
        )

        # Apply Raster Extension to the Asset
        asset_raster_ext = AssetRasterExtension.ext(asset, add_if_missing=True)
        asset_raster_ext.apply(bands=raster_bands)

        # Add eo:bands to Asset
        # Apply EO bands to the asset using AssetEOExtension
        asset_eo_ext = EOExtension.ext(asset, add_if_missing=True)
        asset_eo_ext.apply(bands=eo_bands)

        return item
