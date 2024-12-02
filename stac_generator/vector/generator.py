import logging
import re

import geopandas as gpd
import pystac
from pyproj.crs.crs import CRS

from stac_generator.base.generator import VectorGenerator as BaseVectorGenerator
from stac_generator.vector.schema import VectorConfig

logger = logging.getLogger(__name__)


def extract_epsg(crs: CRS) -> int | None:
    """Extract epsg information from crs object.
    If epsg info can be extracted directly from crs, return that value.
    Otherwise, try to convert the crs info to WKT2 and extract EPSG using regex

    Note that this method may yield unreliable result

    :param crs: crs object
    :type crs: CRS
    :return: epsg information
    :rtype: int | None
    """
    if (result := crs.to_epsg()) is not None:
        return result
    wkt = crs.to_wkt()
    match = re.search(r'ID\["EPSG",(\d+)\]', wkt)
    if match:
        return int(match.group(1))
    return None


class VectorGenerator(BaseVectorGenerator[VectorConfig]):
    """ItemGenerator class that handles vector data with common vector formats - i.e (shp, zipped shp, gpkg, geojson)"""

    def create_item_from_config(self, source_cfg: VectorConfig) -> pystac.Item:
        """Create item from vector config

        :param source_cfg: config information
        :type source_cfg: VectorConfig
        :raises ValueError: if config epsg information is different from epsg information from vector file
        :return: stac metadata of the file described by source_cfg
        :rtype: pystac.Item
        """
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

        return self.df_to_item(raw_df, assets, source_cfg, properties, source_cfg.epsg)
