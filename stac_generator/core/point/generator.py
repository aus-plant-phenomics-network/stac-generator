from __future__ import annotations

import logging

import pystac

from stac_generator._types import CsvMediaType
from stac_generator.core.base.generator import VectorGenerator
from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.base.utils import read_point_asset
from stac_generator.core.point.schema import PointConfig

logger = logging.getLogger(__name__)


class PointGenerator(VectorGenerator[PointConfig]):
    """ItemGenerator class that handles point data in csv format"""

    def create_item_from_config(self, source_config: PointConfig) -> pystac.Item:
        """Create item from source csv config

        :param source_config: config which contains csv metadata
        :type source_config: PointConfig
        :return: stac metadata of the item described in source_config
        :rtype: pystac.Item
        """
        assets = {
            ASSET_KEY: pystac.Asset(
                href=source_config.location,
                description="Raw csv data",
                roles=["data"],
                media_type=CsvMediaType,
            )
        }
        raw_df = read_point_asset(
            source_config.location,
            source_config.X,
            source_config.Y,
            source_config.epsg,
            source_config.Z,
            source_config.T,
            source_config.date_format,
            source_config.column_info,
            source_config.timezone,
        )

        properties = source_config.to_properties()
        return self.df_to_item(
            raw_df,
            assets,
            source_config,
            properties={"stac_generator": properties},
            epsg=source_config.epsg,
            time_column=source_config.T,
        )
