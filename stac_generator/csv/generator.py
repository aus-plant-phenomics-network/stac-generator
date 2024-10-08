import pystac

from stac_generator.base.generator import BaseItemGenerator
from stac_generator.base.schema import STACConfig
from stac_generator.csv.driver import CSVDriver
from stac_generator.csv.schema import CSVConfig, CSVExtension
from stac_generator.csv.utils import group_df, items_from_group_df
from stac_generator.types import CSVMediaType


class CSVItemGenerator(BaseItemGenerator):
    def __init__(
        self, stac_cfg: STACConfig, source_cfg: CSVConfig, driver: CSVDriver | None = None
    ) -> None:
        if not driver:
            driver = CSVDriver(source_cfg)
        super().__init__(source_cfg=source_cfg, driver=driver, stac_cfg=stac_cfg)
        self.stac_cfg: STACConfig
        self.driver: CSVDriver
        self.source_cfg: CSVConfig
        self.asset = pystac.Asset(
            href=self.source_cfg.location,
            description="Raw csv data",
            roles=["data"],
            media_type=CSVMediaType,
        )
        self.properties = {"csv_info": CSVExtension(**self.source_cfg.model_dump())}
        self.prefix = self.stac_cfg.prefix if self.stac_cfg.prefix else self.stac_cfg.id

    def create_items(self) -> list[pystac.Item]:
        raw_df = self.driver.get_data()
        group_map = group_df(raw_df, self.prefix, self.source_cfg.groupby)
        return items_from_group_df(
            group_map,
            self.asset,
            self.source_cfg.epsg,
            self.source_cfg.T,
            self.stac_cfg.datetime,
            self.stac_cfg.start_datetime,
            self.stac_cfg.end_datetime,
            self.properties,
        )
