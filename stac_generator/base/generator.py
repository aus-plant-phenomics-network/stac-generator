import abc
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
    def __class_getitem__(cls, source_type: type) -> type:
        cls.source_type = source_type
        return cls

    def __init__(
        self,
        source_df: DataFrame[DataFrameSchema[T]],
        driver: IODriver,
        catalog_cfg: STACConfig | None = None,
        collection_cfg: STACConfig | None = None,
    ) -> None:
        self.catalog_cfg = catalog_cfg
        self.collection_cfg = collection_cfg
        self.source_df = source_df
        self.driver = driver

    @abc.abstractmethod
    def create_item_from_config(self, source_cfg: T) -> list[pystac.Item]:
        raise NotImplementedError

    def _extract_cfg(self) -> list[T]:
        return [self.source_type(**cast(dict[str, Any], self.source_df.loc[i, :].to_dict())) for i in range(len(self.source_df))]

    @property
    def providers(self) -> list[pystac.Provider] | None:
        if self.collection_cfg and self.collection_cfg.providers:
            return [pystac.Provider.from_dict(item.model_dump()) for item in self.collection_cfg.providers]
        return None

    def create_items(self) -> list[pystac.Item]:
        configs = self._extract_cfg()
        items = []
        for config in configs:
            items.extend(self.create_item_from_config(config))
        return items

    def create_collection(
        self,
        items: list[pystac.Item],
        extent: Extent,
        asset: pystac.Asset,
    ) -> pystac.Collection:
        if self.collection_cfg is None:
            raise ValueError("Generating collection requires non null collection config")
        collection = pystac.Collection(
            id=self.collection_cfg.id,
            description=(
                self.collection_cfg.description
                if self.collection_cfg.description
                else f"Auto-generated collection {self.collection_cfg.id} with stac_generator"
            ),
            extent=extent,
            title=self.collection_cfg.title,
            license=self.collection_cfg.license if self.collection_cfg.license else "proprietory",
            providers=self.providers,
            assets={"source": asset},
        )
        collection.add_items(items)
        return collection

    def create_catalog(self, collection: pystac.Collection) -> pystac.Catalog:
        if self.catalog_cfg is None:
            raise ValueError("Generating catalog requires non null catalog config")
        catalog = pystac.Catalog(id=self.catalog_cfg.id, description=self.catalog_cfg.description, title=self.catalog_cfg.title)
        catalog.add_child(collection)
        return catalog


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
