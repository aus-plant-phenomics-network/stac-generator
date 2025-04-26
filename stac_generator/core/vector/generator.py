from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

import pandas as pd
import pystac

from stac_generator.core.base.generator import VectorGenerator as BaseVectorGenerator
from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.base.utils import (
    get_timezone,
    read_join_asset,
    read_vector_asset,
)
from stac_generator.core.vector.schema import VectorConfig
from stac_generator.exceptions import StacConfigException

if TYPE_CHECKING:
    from pyproj.crs.crs import CRS

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

    def generate(self) -> pystac.Item:
        """Create item from vector config

        :param self.config: config information
        :type self.config: VectorConfig
        :raises ValueError: if config epsg information is different from epsg information from vector file
        :return: stac metadata of the file described by self.config
        :rtype: pystac.Item
        """

        assets = {
            ASSET_KEY: pystac.Asset(
                href=str(self.config.location),
                media_type=pystac.MediaType.GEOJSON
                if self.config.location.endswith(".geojson")
                else "application/x-shapefile",
                roles=["data"],
                description="Raw vector data",
            )
        }
        logger.info(f"Reading vector asset: {self.config.id}")
        time_column = None
        # Only read relevant fields
        columns = [col["name"] if isinstance(col, dict) else col for col in self.config.column_info]
        # Throw exceptions if column_info contains invalid column
        raw_df = read_vector_asset(self.config.location, layer=self.config.layer)

        if columns and not set(columns).issubset(set(raw_df.columns)):
            raise StacConfigException(
                f"Invalid columns for asset - {self.config.location!s}: {set(columns) - set(raw_df.columns)}"
            )

        # Validate EPSG user-input vs extracted
        epsg, _ = extract_epsg(raw_df.crs)
        # Read join file
        if self.config.join_config:
            join_config = self.config.join_config
            logger.info(f"Reading join asset for vector asset: {self.config.id}")
            # Get timezone information
            tzinfo = get_timezone(self.config.timezone, raw_df.to_crs(4326).geometry)
            # Try reading join file and raise errors if columns not provided
            join_df = read_join_asset(
                join_config.file,
                join_config.right_on,
                join_config.date_format,
                join_config.date_column,
                join_config.column_info,
                tzinfo,
            )
            # Try joining the files to validate results:
            raw_df = pd.merge(
                raw_df,
                join_df,
                left_on=join_config.left_on,
                right_on=join_config.right_on,
            )
            # Set asset start and end datetime based on date information
            if join_config.date_column:
                time_column = join_config.date_column

        # Make properties
        properties = self.config.to_properties()

        return self.df_to_item(
            raw_df,
            assets,
            self.config,
            properties={"stac_generator": properties},
            epsg=epsg,
            time_column=time_column,
        )
