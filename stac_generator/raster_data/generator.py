import rasterio
import pandas as pd
import pystac, csv
from pystac.extensions.eo import EOExtension, Band
from pystac.extensions.projection import ProjectionExtension
from typing import List, Dict
import logging

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig
from .schema import RasterSourceConfig

# Map raw band names to STAC-compliant common names
BAND_MAPPING: Dict[str, str] = {
    'red': 'red',
    'green': 'green',
    'blue': 'blue',
    'nir': 'nir',
    'rededge': 'rededge'
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
        if 'epsg' in source_df.columns:
            source_df['epsg'] = source_df['epsg'].astype(int)
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
                
                geometry = {
                    "type": "Polygon",
                    "coordinates": [[
                        [bounds.left, bounds.bottom],
                        [bounds.left, bounds.top],
                        [bounds.right, bounds.top],
                        [bounds.right, bounds.bottom],
                        [bounds.left, bounds.bottom]
                    ]]
                }

                # Create base item
                item = pystac.Item(
                    id=source_cfg.prefix,
                    geometry=geometry,
                    bbox=bbox,
                    datetime=source_cfg.datetime,
                    properties={}  # properties will be managed by extensions
                )

                # Initialize EOExtension and set eo:bands as Band objects
                eo_ext = EOExtension.ext(item, add_if_missing=True)
                eo_bands = []
                for idx, band_info in enumerate(source_cfg.bands, start=1):
                    band = Band.create(
                        name=f"B{idx}",
                        common_name=BAND_MAPPING.get(band_info.name.lower(), None),
                        center_wavelength=float(band_info.wavelength) if band_info.wavelength not in [None, "no band specified"] else None
                    )
                    eo_bands.append(band)

                # Ensure eo:bands is managed by EOExtension only
                eo_ext.bands = eo_bands

                # Update other properties
                item.properties.update({
                    "gsd": float(src.res[0]),
                    "platform": "UAV",
                    "instruments": ["Multispectral Camera"],
                })

                # Add projection extension
                proj_ext = ProjectionExtension.ext(item, add_if_missing=True)
                if source_cfg.epsg != crs.to_epsg():
                    raise ValueError(f"EPSG mismatch: {source_cfg.epsg} vs {crs.to_epsg()}")
                proj_ext.epsg = crs.to_epsg()
                proj_ext.transform = list(transform)[:6]
                proj_ext.shape = [src.height, src.width]

                # Add the asset
                media_type = pystac.MediaType.COG if src.driver.upper() == 'COG' else pystac.MediaType.GEOTIFF
                asset = pystac.Asset(
                    href=str(source_cfg.location),
                    media_type=media_type,
                    roles=["data"],
                    title="Raster Data"
                )
                item.add_asset("data", asset)

                # Add STAC extensions
                item.stac_extensions = [
                    "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
                    "https://stac-extensions.github.io/projection/v1.1.0/schema.json"
                ]

                # Force cleanup of any erroneous eo:bands in item.properties
                if "eo:bands" in item.properties:
                    del item.properties["eo:bands"]

                # Validate the item to check schema compliance
                item.validate()

                return [item]
                
        except Exception as e:
            logging.error(f"Error processing raster file: {e}")
            raise

    @classmethod
    def from_csv(cls, csv_path: str, collection_cfg: StacCollectionConfig, **kwargs):
        df = pd.read_csv(csv_path, quoting=csv.QUOTE_MINIMAL)
        return cls(df, collection_cfg, **kwargs)
