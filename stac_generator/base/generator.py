from typing import cast

import httpx
import pystac

from stac_generator.base.driver import IODriver
from stac_generator.base.schema import LoadConfig, SourceConfig, STACConfig, STACEntityT


class STACGenerator:
    def __init__(self, stac_cfg: STACConfig):
        self.stac_cfg = stac_cfg

    def create_item(self) -> list[pystac.Item]:
        return NotImplemented

    def create_collection(self) -> pystac.Collection:
        return NotImplemented

    def update_collection(self) -> pystac.Collection:
        return NotImplemented

    def create_catalog(self) -> pystac.Catalog:
        return NotImplemented

    def update_catalog(self) -> pystac.Catalog:
        return NotImplemented


class STACLoader:
    @staticmethod
    def _load_from_file(entity: STACEntityT, location: str) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        match entity:
            case "Item":
                return pystac.Item.from_file(location)
            case "ItemCollection":
                return pystac.ItemCollection.from_file(location)
            case "Collection":
                return pystac.Collection.from_file(location)
            case "Catalogue":
                return pystac.Catalog.from_file(location)
            case _:
                raise ValueError(f"Invalid STAC type: {entity}")

    @staticmethod
    def _load_from_api(entity: STACEntityT, api_endpoint: str) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        response = httpx.get(api_endpoint)
        json_data = response.json()
        match entity:
            case "Item":
                return pystac.Item(**json_data)
            case "ItemCollection":
                return pystac.ItemCollection(**json_data)
            case "Collection":
                return pystac.Collection(**json_data)
            case "Catalogue":
                return pystac.Catalog(**json_data)
            case _:
                raise ValueError(f"Invalid STAC type: {entity}")

    @staticmethod
    def from_config(load_cfg: LoadConfig) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        """Get a STAC entity using information from LoadConfig.

        Args:
            load_cfg (LoadConfig): information on entity type, its json path on disk or its remote STAC API endpoint

        Returns:
            pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection: STAC entity as pystac object
        """
        if load_cfg.json_location:
            return STACLoader._load_from_file(load_cfg.entity, load_cfg.json_location)
        return STACLoader._load_from_api(load_cfg.entity, cast(str, load_cfg.stac_api_endpoint))
