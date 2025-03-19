from __future__ import annotations

import json
from typing import Any, cast

import pystac
import rasterio
from pyproj import CRS
from pyproj.transformer import Transformer
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.projection import ItemProjectionExtension, ProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
from shapely import box, to_geojson

from stac_generator.core.base.generator import ItemGenerator
from stac_generator.core.base.utils import calculate_timezone

from .schema import BandInfo, RasterConfig

BAND_MAPPING: dict[str, str] = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "nir": "nir",
    "ms_red": "ms_red",
    "ms_green": "ms_green",
    "red_edge": "rededge",
    "rededge": "rededge",
    "ndvi": "ndvi",
    "ndvi2": "ndvi2",
}


class RasterGenerator(ItemGenerator[RasterConfig]):
    """Raster Generator"""

    @staticmethod
    def create_config(source_config: dict[str, Any]) -> dict[str, Any]:
        with rasterio.open(source_config["location"]) as src:
            band_count = src.count
            bands = []
            for i in range(band_count):
                bands.append(BandInfo(name=f"Band{i}", common_name=f"Band{i}"))
        return RasterConfig(**source_config, band_info=bands).to_properties()

    def create_item_from_config(self, source_config: RasterConfig) -> pystac.Item:
        """Generate Raster Item from config

        :param source_config: raster config - must contain band info
        :type source_config: RasterConfig
        :raises ValueError: if epsg code is provided in config but does not match that extracted from the asset
        :return: generated item
        :rtype: pystac.Item
        """
        with rasterio.open(source_config.location) as src:
            bounds = src.bounds
            transform = src.transform
            crs = cast(CRS, src.crs)
            shape = list(src.shape)

            # Convert to 4326 for bbox and geometry
            transformer = Transformer.from_crs(crs, 4326, always_xy=True)
            minx, miny = transformer.transform(bounds.left, bounds.bottom)
            maxx, maxy = transformer.transform(bounds.right, bounds.top)
            bbox: tuple[float, float, float, float] = (minx, miny, maxx, maxy)

            # Create geometry as Shapely Polygon
            geometry = box(*bbox)
            geometry_geojson = json.loads(to_geojson(geometry))

            # Process datetime
            item_tz = calculate_timezone(geometry)
            item_ts = source_config.get_datetime(item_tz)

            # Validate EPSG
            epsg = crs.to_epsg()
            if source_config.epsg is not None and source_config.epsg != epsg:
                raise ValueError(
                    f"EPSG mismatch: source_config.epsg ({source_config.epsg}) does not match EPSG ({epsg})."
                )

            # Create STAC Item
            # Start datetime and end_datetime are set to be collection datetime for Raster data
            item = pystac.Item(
                id=source_config.id,
                geometry=geometry_geojson,
                bbox=list(bbox),
                datetime=item_ts,
                properties={},
                start_datetime=item_ts,
                end_datetime=item_ts,
            )

            # Projection extension
            proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
            affine_transform = [
                rasterio.transform.from_bounds(*bbox, shape[1], shape[0])[i] for i in range(9)
            ]
            proj_ext.apply(epsg=epsg, wkt2=crs.to_wkt(), shape=shape, transform=affine_transform)

            # Initialize extensions
            EOExtension.ext(item, add_if_missing=True)
            proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
            proj_ext.apply(epsg=crs.to_epsg(), shape=shape, transform=list(transform)[:9])

            # Create EO and Raster bands
            eo_bands = []
            raster_bands = []
            for band_info in source_config.band_info:
                eo_band = Band.create(
                    name=band_info["name"].lower(),
                    common_name=BAND_MAPPING.get(band_info.get("common_name", "").lower(), None),
                    center_wavelength=band_info.get("wavelength", None),
                    description=band_info.get(
                        "description",
                        "Common name: "
                        + BAND_MAPPING.get(
                            band_info.get("common_name", "unknown").lower(), "unknown"
                        ),
                    ),
                )
                eo_bands.append(eo_band)

                raster_band = RasterBand.create(
                    nodata=band_info.get("nodata", 0),
                    data_type=DataType(band_info.get("data_type", "uint16")),
                )
                raster_bands.append(raster_band)

            eo_ext = EOExtension.ext(item, add_if_missing=True)
            eo_ext.apply(bands=eo_bands, cloud_cover=0.0, snow_cover=0.0)

            # Create Asset and Add to Item
            asset = pystac.Asset(
                href=source_config.location,
                media_type=pystac.MediaType.GEOTIFF,
                roles=["data"],
                title="Raster Data",
            )
            item.add_asset("data", asset)

            # Apply Raster Extension to the Asset
            raster_ext = AssetRasterExtension.ext(asset, add_if_missing=True)
            raster_ext.apply(bands=raster_bands)

            # Add eo:bands to Asset
            # Apply EO bands to the asset using AssetEOExtension
            asset_eo_ext = EOExtension.ext(asset, add_if_missing=True)
            asset_eo_ext.apply(bands=eo_bands)

            return item
