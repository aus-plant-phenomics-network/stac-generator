import rasterio
import pandas as pd
import pystac
from pystac.extensions.eo import EOExtension, Band
from pystac.extensions.projection import ProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, RasterBand, DataType
from shapely.geometry import mapping
from typing import List, Dict
import logging
import csv
from shapely.geometry import Polygon, mapping

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig
from .schema import RasterSourceConfig


# In case the config file has different names for bands
# (lowercase/uppercase/space in between etc)
BAND_MAPPING: Dict[str, str] = {
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
        super().__init__(
            source_df=source_df,
            collection_cfg=collection_cfg,
            catalog_cfg=catalog_cfg,
            href=href,
        )

    def create_item_from_config(self, source_cfg: RasterSourceConfig) -> List[pystac.Item]:
        logging.info(f"Processing raster from: {source_cfg.location}")

        try:
            with rasterio.open(source_cfg.location) as src:
                bounds = src.bounds
                bbox = [bounds.left, bounds.bottom, bounds.right, bounds.top]
                transform = src.transform
                crs = src.crs
                shape = [src.height, src.width]

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

                # Create STAC Item
                item = pystac.Item(
                    id=source_cfg.prefix,
                    geometry=geometry_geojson,
                    bbox=bbox,
                    datetime=source_cfg.datetime,
                    properties={
                        "eo:snow_cover": 0,
                        "eo:cloud_cover": 0,
                        "proj:epsg": crs.to_epsg(),
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

                    raster_band = RasterBand.create(nodata=0, data_type=DataType.UINT16)
                    raster_bands.append(raster_band)

                item.properties["eo:bands"] = [band.to_dict() for band in eo_bands]

                # Create Asset and Add to Item
                asset = pystac.Asset(
                    href=source_cfg.location,
                    media_type=pystac.MediaType.GEOTIFF,
                    roles=["data"],
                    title="Raster Data",
                )
                item.add_asset("image", asset)

                # Apply Raster Extension to the Asset
                raster_ext = AssetRasterExtension.ext(asset, add_if_missing=True)
                raster_ext.apply(bands=raster_bands)

                # Add eo:bands to Asset
                asset.extra_fields["eo:bands"] = [band.to_dict() for band in eo_bands]

                # Add STAC Extensions
                item.stac_extensions = [
                    "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
                    "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
                    "https://stac-extensions.github.io/raster/v1.1.0/schema.json",
                ]

                # Validate the Item
                item.validate()
                return [item]

        except Exception as e:
            logging.error(f"Error processing raster file: {e}")
            raise

    @classmethod
    def from_csv(cls, csv_path: str, collection_cfg: StacCollectionConfig, **kwargs):
        df = pd.read_csv(csv_path, quoting=csv.QUOTE_MINIMAL)
        return cls(df, collection_cfg, **kwargs)
