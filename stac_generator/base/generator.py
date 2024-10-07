import abc
from collections.abc import Sequence

import pystac

from stac_generator.base.driver import IODriver
from stac_generator.base.schema import LoadConfig, SourceConfig, STACConfig, STACEntityT


class STACGenerator:
    def __init__(self, source_cfg: SourceConfig, stac_cfg: STACConfig, driver: IODriver, load_cfg: Sequence[LoadConfig] | None = None):
        self.driver = driver
        self.source_cfg = source_cfg
        self.stac_cfg = stac_cfg
        self.load_cfg = load_cfg

    def valid_load_cfg_non_null(self) -> None:
        if self.load_cfg is None:
            raise ValueError("Load information must be provided for load operation")

    def create_item(self) -> list[pystac.Item]:
        return NotImplemented

    def read_item(self) -> list[pystac.Item | pystac.ItemCollection]:
        return NotImplemented

    def read_item_collection_from_file(self) -> pystac.ItemCollection:
        return NotImplemented

    def read_item_from_api(self) -> pystac.Item:
        return NotImplemented

    def create_collection(self) -> pystac.Collection:
        return NotImplemented

    def update_collection(self) -> pystac.Collection:
        return NotImplemented

    def read_collection_from_file(self) -> pystac.Collection:
        return NotImplemented

    def read_collection_from_api(self) -> pystac.Collection:
        return NotImplemented

    def create_catalog(self) -> pystac.Catalog:
        return NotImplemented

    def update_catalog(self) -> pystac.Catalog:
        return NotImplemented

    def read_catalog_from_file(self) -> pystac.Catalog:
        return NotImplemented

    def read_catalog_from_api(self) -> pystac.Catalog:
        return NotImplemented
