from __future__ import annotations

import logging

import pandas as pd
import pystac

from stac_generator.core.base.generator import BaseVectorGenerator
from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.base.utils import (
    extract_epsg,
    get_timezone,
    read_join_asset,
    read_vector_asset,
)
from stac_generator.core.vector.schema import VectorConfig
from stac_generator.exceptions import StacConfigException

logger = logging.getLogger(__name__)


class VectorGenerator(BaseVectorGenerator[VectorConfig]):
    """ItemGenerator class that handles vector data with common vector formats - i.e (shp, zipped shp, gpkg, geojson)"""

    def generate(self) -> pystac.Item:
        """Create a STAC Item from a VectorConfig

        Raises:
            StacConfigException: if the stac config fails a validation check

        Returns:
            pystac.Item: generated STAC Item
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
                f"Invalid columns for asset - {self.config.location!s}: {set(columns) - set(raw_df.columns)}. The config describes a column that is not present in the raw asset. Fix this error by removing the column info entry or changing the entry to an existing column."
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
        return self.df_to_item(
            raw_df,
            assets,
            self.config,
            properties=self.config.to_properties(),
            epsg=epsg,
            time_column=time_column,
        )
