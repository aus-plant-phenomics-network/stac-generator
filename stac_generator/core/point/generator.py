from __future__ import annotations

import logging

import pystac

from stac_generator._types import CsvMediaType
from stac_generator.core.base.generator import BaseVectorGenerator
from stac_generator.core.base.schema import ASSET_KEY
from stac_generator.core.base.utils import read_point_asset
from stac_generator.core.point.schema import PointConfig

logger = logging.getLogger(__name__)


class PointGenerator(BaseVectorGenerator[PointConfig]):
    """ItemGenerator class that handles point data in csv format"""

    def generate(self) -> pystac.Item:
        """Generate a STAC Item based on provided point config

        Returns:
            pystac.Item: generated STAC Item
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

        return self.df_to_item(
            raw_df,
            assets,
            self.config,
            properties=self.config.to_properties(),
            epsg=self.config.epsg,
            time_column=self.config.T,
        )
