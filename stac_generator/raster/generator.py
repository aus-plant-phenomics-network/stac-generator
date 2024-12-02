from __future__ import annotations

from typing import cast

import pystac
import rasterio
from pyproj import CRS
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.projection import ItemProjectionExtension, ProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
from shapely.geometry import mapping

from stac_generator.base.generator import ItemGenerator
from stac_generator.base.utils import calculate_timezone

from .schema import RasterConfig

BAND_MAPPING: dict[str, str] = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "nir": "nir",
    "rededge": "rededge",
    "ndvi": "ndvi",
    "ndvi2": "ndvi2",
}


class RasterGenerator(ItemGenerator[RasterConfig]):
    def create_item_from_config(self, source_cfg: RasterConfig) -> pystac.Item:
        with rasterio.open(source_cfg.location) as src:
            bounds = src.bounds
            bbox: tuple[float, float, float, float] = (
                bounds.left,
                bounds.bottom,
                bounds.right,
                bounds.top,
            )
            transform = src.transform
            crs = cast(CRS, src.crs)
            shape = src.shape

            # Create geometry as Shapely Polygon
            geometry = RasterGenerator.bounding_geometry(bbox)
            geometry_geojson = mapping(geometry)

            # Process datetime
            item_tz = calculate_timezone(bbox, crs)
            item_ts = source_cfg.get_datetime(item_tz)

            # Validate EPSG
            epsg = crs.to_epsg()
            if source_cfg.epsg != epsg:
                raise ValueError(
                    f"EPSG mismatch: source_cfg.epsg ({source_cfg.epsg}) does not match EPSG ({epsg})."
                )

            # Create STAC Item
            item = pystac.Item(
                id=source_cfg.id,
                geometry=geometry_geojson,
                bbox=cast(list[float], bbox),
                datetime=item_ts,
                properties={},
            )

            # Projection extension
            proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
            affine_transform = [
                rasterio.transform.from_bounds(*bbox, shape[1], shape[0])[i] for i in range(9)
            ]
            proj_ext.apply(epsg=epsg, shape=shape, transform=affine_transform)

            # Initialize extensions
            EOExtension.ext(item, add_if_missing=True)
            proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
            proj_ext.apply(epsg=crs.to_epsg(), shape=shape, transform=list(transform)[:9])

            # Create EO and Raster bands
            eo_bands = []
            raster_bands = []
            for band_info in source_cfg.bands:
                eo_band = Band.create(
                    name=BAND_MAPPING[band_info.name.lower()],
                    common_name=BAND_MAPPING.get(band_info.name.lower(), None),
                    center_wavelength=band_info.wavelength,
                    description=f"Common name: {BAND_MAPPING.get(band_info.name.lower(), 'unknown')}",
                )
                eo_bands.append(eo_band)

                raster_band = RasterBand.create(
                    nodata=band_info.nodata or 0,
                    data_type=DataType(band_info.data_type or "uint16"),
                )
                raster_bands.append(raster_band)

            eo_ext = EOExtension.ext(item, add_if_missing=True)
            eo_ext.apply(bands=eo_bands, cloud_cover=0.0, snow_cover=0.0)

            # Create Asset and Add to Item
            asset = pystac.Asset(
                href=source_cfg.location,
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
