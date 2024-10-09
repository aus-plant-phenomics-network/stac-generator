import pandas as pd
import pystac

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig
from stac_generator.csv.driver import CsvDriver
from stac_generator.csv.schema import CsvConfig, CsvExtension
from stac_generator.csv.utils import group_df, items_from_group_df
from stac_generator.types import CsvMediaType


class CsvGenerator(StacGenerator[CsvConfig]):
    def __init__(
        self,
        source_df: pd.DataFrame,
        collection_cfg: StacCollectionConfig,
        catalog_cfg: StacCatalogConfig | None = None,
        href: str | None = None,
    ) -> None:
        super().__init__(
            source_df=source_df,
            collection_cfg=collection_cfg,
            catalog_cfg=catalog_cfg,
            href=href,
            driver=CsvDriver,
        )
        self.driver: type[CsvDriver]

    def create_item_from_config(self, source_cfg: CsvConfig) -> list[pystac.Item]:
        asset = pystac.Asset(
            href=source_cfg.location,
            description="Raw csv data",
            roles=["data"],
            media_type=CsvMediaType,
        )
        raw_df = self.driver(source_cfg).get_data()
        group_map = group_df(raw_df, source_cfg.prefix, source_cfg.groupby)
        properties = CsvExtension.model_validate(source_cfg, from_attributes=True).model_dump()
        return items_from_group_df(
            group_map,
            asset,
            source_cfg.epsg,
            source_cfg.T,
            source_cfg.datetime,
            source_cfg.start_datetime,
            source_cfg.end_datetime,
            properties,
        )
