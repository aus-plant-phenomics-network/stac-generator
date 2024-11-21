import csv
import json
import logging
from typing import Any

import pandas as pd
import pystac
import rasterio
from pyproj import Transformer
from pystac.extensions.eo import Band, EOExtension
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
from shapely.geometry import Point, Polygon, mapping
from timezonefinder import TimezoneFinder

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig

from .schema import RasterSourceConfig

BAND_MAPPING: dict[str, str] = {
    "red": "red",
    "green": "green",
    "blue": "blue",
    "nir": "nir",
    "rededge": "rededge",
    "ndvi": "ndvi",
    "ndvi2": "ndvi2",
}


class RasterGenerator(StacGenerator[RasterSourceConfig]):
    source_type = RasterSourceConfig

    def __init__(
        self,
        source_df: pd.DataFrame,
        collection_cfg: StacCollectionConfig,
        catalog_cfg: StacCatalogConfig | None = None,
        href: str | None = None,
    ) -> None:
        source_df = source_df.reset_index(drop=True)

        if "epsg" in source_df.columns:
            source_df["epsg"] = source_df["epsg"].astype(int)

        if "bands" in source_df.columns:
            source_df["bands"] = source_df["bands"].apply(self.parse_bands)

        super().__init__(
            source_df=source_df,
            collection_cfg=collection_cfg,
            catalog_cfg=catalog_cfg,
            href=href,
        )

    @staticmethod
    def parse_bands(bands: Any) -> Any:
        if isinstance(bands, str):
            try:
                return json.loads(bands)
            except json.JSONDecodeError as e:
                raise ValueError(f"Error parsing 'bands': {bands}") from e
        return bands

    def get_timezone_from_geotiff(self, src: rasterio.io.DatasetReader) -> str:
        """Determine the timezone from the GeoTIFF file's centroid."""
        # Extract the bounding box
        bounds = src.bounds
        centroid = Point((bounds.left + bounds.right) / 2, (bounds.bottom + bounds.top) / 2)

        # Transform the centroid to EPSG:4326
        transformer = Transformer.from_crs(src.crs, "EPSG:4326", always_xy=True)
        lon, lat = transformer.transform(centroid.x, centroid.y)

        # Validate the reprojected longitude and latitude
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            raise ValueError(f"Reprojected coordinates out of bounds: lon={lon}, lat={lat}")

        # Use TimezoneFinder to get the timezone
        tf = TimezoneFinder()
        timezone_str = tf.timezone_at(lng=lon, lat=lat)

        if timezone_str:
            return timezone_str
        raise ValueError(f"Could not determine timezone for coordinates: lon={lon}, lat={lat}")

    def create_item_from_config(self, source_cfg: RasterSourceConfig) -> list[pystac.Item]:
        logging.info("Processing raster from: %s", source_cfg.location)

        try:
            with rasterio.open(source_cfg.location) as src:
                bounds = src.bounds
                bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                transform = src.transform
                crs = src.crs
                shape = src.shape

                # Get the timezone using the GeoTIFF's centroid
                file_timezone = self.get_timezone_from_geotiff(src)

                # Create geometry as Shapely Polygon
                geometry = Polygon(
                    [
                        (bounds.left, bounds.bottom),
                        (bounds.left, bounds.top),
                        (bounds.right, bounds.top),
                        (bounds.right, bounds.bottom),
                        (bounds.left, bounds.bottom),
                    ]
                )
                geometry_geojson = mapping(geometry)

                if source_cfg.datetime is None:
                    raise ValueError("source_cfg.datetime cannot be None")

                # Ensure datetime is timezone-aware
                if source_cfg.datetime.tzinfo is None:
                    datetime_aware = source_cfg.datetime.replace(tzinfo=file_timezone)
                else:
                    datetime_aware = source_cfg.datetime

                epsg = crs.to_epsg()
                if source_cfg.epsg != epsg:
                    raise ValueError(
                        f"EPSG mismatch: source_cfg.epsg ({source_cfg.epsg}) does not match EPSG ({epsg})."
                    )

                # Create STAC Item
                item = pystac.Item(
                    id=source_cfg.prefix,
                    geometry=geometry_geojson,
                    bbox=bbox,
                    datetime=datetime_aware,
                    properties={
                        "proj:epsg": epsg,
                        "proj:shape": shape,
                        "proj:transform": list(transform)[:9],
                    },
                )

                # Initialize extensions
                EOExtension.ext(item, add_if_missing=True)
                proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
                proj_ext.apply(epsg=crs.to_epsg(), shape=shape, transform=list(transform)[:9])

                # Create EO and Raster bands
                eo_bands = []
                raster_bands = []
                for idx, band_info in enumerate(source_cfg.bands, start=1):
                    eo_band = Band.create(
                        name=f"B{idx}",
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

                # Validate the Item
                item.validate()
                return [item]

        except Exception as e:
            logging.error("Error processing raster file %s: %s", source_cfg.location, e)
            raise RuntimeError("Failed to process raster file") from e

    @classmethod
    def from_csv(
        cls: type[StacGenerator], csv_path: str, collection_cfg: StacCollectionConfig, **kwargs: Any
    ) -> StacGenerator:
        df = pd.read_csv(csv_path, quoting=csv.QUOTE_MINIMAL)
        return cls(df, collection_cfg, **kwargs)
