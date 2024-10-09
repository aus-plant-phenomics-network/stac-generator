import pystac
from pandera.typing.pandas import DataFrame

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import DataFrameSchema, StacCatalogConfig, StacCollectionConfig
from stac_generator.csv.driver import CSVDriver
from stac_generator.csv.schema import CSVConfig, CSVExtension
from stac_generator.csv.utils import group_df, items_from_group_df
from stac_generator.types import CSVMediaType

__all__ = ("CSVGenerator",)


class CSVGenerator(StacGenerator[CSVConfig]):
    def __init__(
        self,
        source_df: DataFrame[DataFrameSchema[CSVConfig]],
        catalog_cfg: StacCatalogConfig | None = None,
        collection_cfg: StacCollectionConfig | None = None,
    ) -> None:
        super().__init__(source_df, CSVDriver, catalog_cfg, collection_cfg)

    def create_item_from_config(self, source_cfg: CSVConfig) -> list[pystac.Item]:
        asset = pystac.Asset(
            href=source_cfg.location,
            description="Raw csv data",
            roles=["data"],
            media_type=CSVMediaType,
        )
        raw_df = self.driver(source_cfg).get_data()
        group_map = group_df(raw_df, source_cfg.prefix, source_cfg.groupby)
        properties = CSVExtension.model_validate(source_cfg, from_attributes=True).model_dump()
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
