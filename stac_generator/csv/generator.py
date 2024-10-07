import pystac

from stac_generator.base.generator import STACItemGenerator
from stac_generator.csv.driver import CSVDriver
from stac_generator.csv.schema import CSVConfig
from stac_generator.csv.utils import group_df, items_from_group_df
from stac_generator.typing import CSVMediaType


class CSVItemGenerator(STACItemGenerator):
    def __init__(self, config: CSVConfig, driver: CSVDriver | None = None) -> None:
        if not driver:
            driver = CSVDriver(config)
        super().__init__(config, driver)
        self.config: CSVConfig
        self.driver: CSVDriver
        self.asset = pystac.Asset(
            href=self.config.location,
            description="Raw csv data",
            roles=["data"],
            media_type=CSVMediaType,
        )
        self.prefix = self.config.prefix if self.config.prefix else self.config.id

    def create_items(self) -> list[pystac.Item]:
        raw_df = self.driver.get_data()
        group_map = group_df(raw_df, self.prefix, self.config.groupby)
        return items_from_group_df(
            group_map,
            self.asset,
            self.config.epgs,
            self.config.T,
            self.config.datetime,
            self.config.start_datetime,
            self.config.end_datetime,
            self.config.bands,
        )
