import logging
import re

import geopandas as gpd
import pystac
from pyproj.crs.crs import CRS

from stac_generator.base.generator import VectorGenerator as BaseVectorGenerator
from stac_generator.vector.schema import VectorConfig

logger = logging.getLogger(__name__)


def extract_epsg(crs: CRS) -> int | None:
    if (result := crs.to_epsg()) is not None:
        return result
    wkt = crs.to_wkt()
    match = re.search(r'ID\["EPSG",(\d+)\]', wkt)
    if match:
        return int(match.group(1))
    return None


class VectorGenerator(BaseVectorGenerator[VectorConfig]):
    def create_item_from_config(self, source_cfg: VectorConfig) -> pystac.Item:
        assets = {
            "data": pystac.Asset(
                href=str(source_cfg.location),
                media_type=pystac.MediaType.GEOJSON
                if source_cfg.location.endswith(".geojson")
                else "application/x-shapefile",
                roles=["data"],
                description="Raw vector data",
            )
        }
        logger.debug(f"Reading file from {source_cfg.location}")
        raw_df = gpd.read_file(source_cfg.location)

        if extract_epsg(raw_df.crs) != source_cfg.epsg:
            raise ValueError(
                f"Source crs: {raw_df.crs} does not match config epsg: {source_cfg.epsg}"
            )

        properties = {"epsg": source_cfg.epsg}

        return self.df_to_item(raw_df, assets, source_cfg, properties, None, source_cfg.epsg)
