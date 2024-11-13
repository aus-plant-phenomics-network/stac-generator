from typing import Any

import pystac

from stac_generator._types import CsvMediaType
from stac_generator.base.generator import ItemGenerator
from stac_generator.csv.schema import CsvConfig, CsvExtension
from stac_generator.csv.utils import df_to_item, read_csv


class CsvGenerator(ItemGenerator[CsvConfig]):
    def __init__(
        self,
        configs: list[dict[str, Any]],
    ) -> None:
        super().__init__(
            configs=configs,
        )

    def create_item_from_config(self, source_cfg: CsvConfig) -> pystac.Item:
        assets = {
            "data": pystac.Asset(
                href=source_cfg.location,
                description="Raw csv data",
                roles=["data"],
                media_type=CsvMediaType,
            )
        }
        raw_df = read_csv(
            source_cfg.location,
            source_cfg.X,
            source_cfg.Y,
            source_cfg.epsg,
            source_cfg.Z,
            source_cfg.T,
            source_cfg.date_format,
            source_cfg.column_info,
        )

        properties = CsvExtension.model_validate(source_cfg, from_attributes=True).model_dump()
        return df_to_item(raw_df, assets, source_cfg, properties)
