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

    def generate(self) -> pystac.Item:
        """Create item from source csv config

        :param self.config: config which contains csv metadata
        :type self.config: PointConfig
        :return: stac metadata of the item described in self.config
        :rtype: pystac.Item
        """
        assets = {
            ASSET_KEY: pystac.Asset(
                href=self.config.location,
                description="Raw csv data",
                roles=["data"],
                media_type=CsvMediaType,
            )
        }
        logger.info(f"Reading point asset: {self.config.id}")
        raw_df = read_point_asset(
            self.config.location,
            self.config.X,
            self.config.Y,
            self.config.epsg,
            self.config.Z,
            self.config.T,
            self.config.date_format,
            self.config.column_info,
            self.config.timezone,
        )

        properties = self.config.to_properties()
        return self.df_to_item(
            raw_df,
            assets,
            self.config,
            properties={"stac_generator": properties},
            epsg=self.config.epsg,
            time_column=self.config.T,
        )
