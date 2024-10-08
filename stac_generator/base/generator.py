from typing import Any, Generic, cast

import httpx
import pystac
from pandera.typing import DataFrame
from pystac.collection import Extent

from stac_generator.base.driver import IODriver
from stac_generator.base.schema import DataFrameSchema, LoadConfig, STACConfig, T
from stac_generator.types import STACEntityT


class STACGenerator(Generic[T]):
    source_type: type[T]

    @classmethod
    def __class_getitem__(cls, model_type: type) -> type:
        cls.source_type = model_type
        return cls

    def __init__(
        self,
        stac_cfg: STACConfig,
        source_df: DataFrame[DataFrameSchema[T]],
        driver: IODriver,
    ) -> None:
        self.stac_cfg = stac_cfg
        self.source_df = source_df
        self.driver = driver

    def create_item(self, source_cfg: T) -> list[pystac.Item]:
        return NotImplemented

    def extract_cfg(self) -> list[T]:
        return [
            self.source_type(**cast(dict[str, Any], self.source_df.loc[i, :].to_dict()))
            for i in range(len(self.source_df))
        ]

    @property
    def providers(self) -> list[pystac.Provider] | None:
        if self.stac_cfg.providers:
            return [
                pystac.Provider.from_dict(item.model_dump()) for item in self.stac_cfg.providers
            ]
        return None

    def create_collection(
        self,
        items: list[pystac.Item],
        extent: Extent,
        asset: pystac.Asset,
    ) -> pystac.Collection:
        collection = pystac.Collection(
            id=self.stac_cfg.id,
            description=self.stac_cfg.description
            if self.stac_cfg.description
            else f"Auto-generated collection {self.stac_cfg.id} with stac_generator",
            extent=extent,
            title=self.stac_cfg.title,
            license=self.stac_cfg.license if self.stac_cfg.license else "proprietory",
            providers=self.providers,
            assets={"source": asset},
        )
        collection.add_items(items)
        return collection


class STACLoader:
    @staticmethod
    def _load_from_file(
        entity: STACEntityT, location: str
    ) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
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
    def _load_from_api(
        entity: STACEntityT, api_endpoint: str
    ) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
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
    def from_config(
        load_cfg: LoadConfig,
    ) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        """Get a STAC entity using information from load_cfg

        :param load_cfg: load information
        :type load_cfg: LoadConfig
        :return: pystac entity
        :rtype: pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection
        """
        if load_cfg.json_location:
            return STACLoader._load_from_file(load_cfg.entity, load_cfg.json_location)
        return STACLoader._load_from_api(load_cfg.entity, cast(str, load_cfg.stac_api_endpoint))
