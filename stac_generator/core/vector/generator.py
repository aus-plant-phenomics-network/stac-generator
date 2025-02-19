import logging
import re
from typing import Any

import geopandas as gpd
import pystac
from pyproj.crs.crs import CRS

from stac_generator.core.base.generator import VectorGenerator as BaseVectorGenerator
from stac_generator.core.base.schema import ColumnInfo
from stac_generator.core.vector.schema import VectorConfig

logger = logging.getLogger(__name__)


def extract_epsg(crs: CRS) -> tuple[int, bool]:
    """Extract epsg information from crs object.
    If epsg info can be extracted directly from crs, return that value.
    Otherwise, try to convert the crs info to WKT2 and extract EPSG using regex

    Note that this method may yield unreliable result

    :param crs: crs object
    :type crs: CRS
    :return: epsg information
    :rtype: tuple[int, bool] - epsg code and reliability flag
    """
    if (result := crs.to_epsg()) is not None:
        return (result, True)
    # Handle WKT1 edge case
    wkt = crs.to_wkt()
    match = re.search(r'ID\["EPSG",(\d+)\]', wkt)
    if match:
        return (int(match.group(1)), True)
    # No match - defaults to 4326
    logger.warning(
        "Cannot determine epsg from vector file. Either provide it in the config or change the source file. Defaults to 4326 but can be incorrect."
    )
    return (4326, False)


class VectorGenerator(BaseVectorGenerator[VectorConfig]):
    """ItemGenerator class that handles vector data with common vector formats - i.e (shp, zipped shp, gpkg, geojson)"""

    @staticmethod
    def create_config(source_cfg: dict[str, Any]) -> dict[str, Any]:
        if not hasattr(source_cfg, "layers"):
            try:
                raw_df = gpd.read_file(source_cfg["location"])
            except Exception as e:
                raise ValueError(
                    "Compressed zip contains multiple vector layers. Please specify a layer in the original config"
                ) from e
        else:
            raw_df = gpd.read_file(source_cfg["location"], layer=getattr(source_cfg, "layer", None))
        columns = []
        for name in raw_df.columns:
            if name != "geometry":
                columns.append(ColumnInfo(name=name, description=f"{name}_description"))
        return VectorConfig(**source_cfg, column_info=columns).model_dump(
            mode="json", exclude_none=True
        )

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

        # Only read relevant fields
        if isinstance(source_cfg.column_info, list):
            columns = [
                col["name"] if isinstance(col, dict) else col for col in source_cfg.column_info
            ]
        else:
            columns = None
        raw_df = gpd.read_file(source_cfg.location, columns=columns, layer=source_cfg.layer)

        # Validate EPSG user-input vs extracted
        epsg, reliable = extract_epsg(raw_df.crs)
        if source_cfg.epsg is not None:
            if reliable and epsg != source_cfg.epsg:
                raise ValueError(
                    f"Source crs: {raw_df.crs} does not match config epsg: {source_cfg.epsg}"
                )
            epsg = source_cfg.epsg

        properties = source_cfg.model_dump(
            include={"column_info", "title", "description", "layer"},
            exclude_unset=True,
            exclude_none=True,
        )

        return self.df_to_item(raw_df, assets, source_cfg, properties, epsg)
