import abc
from typing import Any, Generic, cast

import httpx
import pandas as pd
import pystac
from pystac.collection import Extent

from stac_generator.base.driver import IODriver
from stac_generator.base.schema import (
    LoadConfig,
    StacCatalogConfig,
    StacCollectionConfig,
    T,
)
from stac_generator.base.utils import extract_spatial_extent, extract_temporal_extent
from stac_generator.types import StacEntityT


class StacGenerator(Generic[T]):
    source_type: type[T]
    """SourceConfig subclass that contains information used for parsing the source file"""

    @classmethod
    def __class_getitem__(cls, source_type: type) -> type:
        kwargs = {"source_type": source_type}
        return type(f"StacGenerator[{source_type.__name__}]", (StacGenerator,), kwargs)

    def __init__(
        self,
        source_df: pd.DataFrame,
        collection_cfg: StacCollectionConfig,
        catalog_cfg: StacCatalogConfig | None = None,
        href: str | None = None,
        driver: type[IODriver] | None = None,
    ) -> None:
        """Base STACGenerator object. Users should extend this class for handling different file extensions.
        Please see CsvStacGenerator source code.

        :param source_df: source data config
        :type source_df: pd.DataFrame
        :param collection_cfg: collection config for generating collection. Required if the intention is to save the catalog to disk or POST to an API, defaults to None
        :type collection_cfg: StacCollectionConfig
        :param catalog_cfg: catalog config for generating catalog. Required if the intention is to save the catalog to disk or POST to an API, defaults to None
        :type catalog_cfg: StacCatalogConfig | None, optional
        :param href: catalog href for serialisation.
        :type href: str | None, optional
        :param driver: driver that handles T file extension using config for extension type T. Note that this field is not required
        :type driver: type[IODriver] | None, optional

        """
        self.collection_cfg = collection_cfg
        self.catalog_cfg = (
            catalog_cfg
            if catalog_cfg
            else StacCatalogConfig(
                id=collection_cfg.id,
                title=collection_cfg.title,
                description=collection_cfg.description,
            )
        )
        self.source_df = source_df
        self.driver = driver
        self.configs = [
            self.source_type(**cast(dict[str, Any], self.source_df.loc[i, :].to_dict()))
            for i in range(len(self.source_df))
        ]
        self.href = href

    @abc.abstractmethod
    def create_item_from_config(self, source_cfg: T) -> list[pystac.Item]:
        """Abstract method that handles `pystac.Item` generation from the appropriate config"""
        raise NotImplementedError

    @staticmethod
    def extract_extent(
        items: list[pystac.Item], collection_cfg: StacCollectionConfig | None = None
    ) -> Extent:
        return Extent(extract_spatial_extent(items), extract_temporal_extent(items, collection_cfg))

    def _create_collection_from_items(
        self,
        items: list[pystac.Item],
        collection_cfg: StacCollectionConfig | None = None,
    ) -> pystac.Collection:
        if collection_cfg is None:
            raise ValueError("Generating collection requires non null collection config")
        collection = pystac.Collection(
            id=collection_cfg.id,
            description=(
                collection_cfg.description
                if collection_cfg.description
                else f"Auto-generated collection {collection_cfg.id} with stac_generator"
            ),
            extent=self.extract_extent(items, collection_cfg),
            title=collection_cfg.title,
            license=collection_cfg.license if collection_cfg.license else "proprietary",
            providers=[
                pystac.Provider.from_dict(item.model_dump()) for item in collection_cfg.providers
            ]
            if collection_cfg.providers
            else None,
        )
        collection.add_items(items)
        return collection

    def _create_catalog_from_collection(
        self, collection: pystac.Collection, catalog_cfg: StacCatalogConfig | None = None
    ) -> pystac.Catalog:
        if catalog_cfg is None:
            raise ValueError("Generating catalog requires non null catalog config")
        catalog = pystac.Catalog(
            id=catalog_cfg.id,
            description=catalog_cfg.description,
            title=catalog_cfg.title,
        )
        catalog.add_child(collection)
        return catalog

    def create_items(self) -> list[pystac.Item]:
        """Generate STAC Items from source dataframe

        :return: list of generated STAC Item
        :rtype: list[pystac.Item]
        """
        items = []
        for config in self.configs:
            items.extend(self.create_item_from_config(config))
        return items

    def create_collection(self) -> pystac.Collection:
        """Generate STAC Collection that includes all STAC Items from source dataframe

        collection_cfg must be provided to constructor for this method to work

        :return: STAC Collection that includes all generated STAC Items
        :rtype: pystac.Collection
        """
        items = self.create_items()
        return self._create_collection_from_items(items, self.collection_cfg)

    def create_catalog(self) -> pystac.Catalog:
        """Generate STAC Catalog that includes a STAC Collection containing all STAC Item generated from
        source dataframe

        Both collection_cfg and catalog_cfg must be provided for this method to work

        :return: STAC Catalog
        :rtype: pystac.Catalog
        """
        collection = self.create_collection()
        return self._create_catalog_from_collection(collection, self.catalog_cfg)

    def generate_collection_and_save(self, href: str) -> None:
        """Generate STAC Collection and save to disk.

        This is a convenient method
        that combines `self.create_collection` and `collection.normalize_and_save(href)`


        :param href: disk location of the generated collection
        :type href: str
        """
        collection = self.create_collection()
        collection.normalize_hrefs(href)
        collection.validate_all()
        collection.save()

    def generate_catalog_and_save(self, href: str | None) -> None:
        """Write the catalog generated from source dataframe to local disk

        If `href` is not provided, will attemp to use `href` under `StacCatalogConfig`

        :param href: disk location
        :type href: str | None
        :raises ValueError: if href parameter is not provided as method argument or config attribute
        """
        if not href and not (self.catalog_cfg and self.href):
            raise ValueError("Href must be provided as argument or under catalog config")
        catalog = self.create_catalog()
        href = href if href is not None else cast(str, self.href)
        catalog.normalize_hrefs(href)
        catalog.validate_all()
        catalog.save()

    async def write_to_api(self, href: str | None = None) -> None:
        """Write the catalog generated from source dataframe to an href

        If href is not provided, will attempt to use the href under `StacCatalogConfig`

        :param href: STAC api href, defaults to None
        :type href: str | None, optional
        :raises ValueError: if href parameter is not provided as method argument or config attribute
        """
        if not href and not (self.catalog_cfg and self.href):
            raise ValueError("href must be provided as argument or to catalog config")
        catalog = self.create_catalog()
        href = href if href is not None else cast(str, self.href)
        catalog.normalize_hrefs(href)
        catalog.validate_all()
        async with httpx.AsyncClient() as client:
            for collection in catalog.get_collections():
                for item in collection.get_all_items():
                    await client.post(
                        f"{href}/collection/{item.collection_id}/items/{item.id}",
                        json=item.to_dict(),
                    )
                await client.post(f"{href}/collection/{collection.id}", json=collection.to_dict())


class StacLoader:
    @staticmethod
    def _load_from_file(
        entity: StacEntityT, location: str
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
                raise ValueError(f"Invalid Stac type: {entity}")

    @staticmethod
    def _load_from_api(
        entity: StacEntityT, api_href: str
    ) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        response = httpx.get(api_href)
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
                raise ValueError(f"Invalid Stac type: {entity}")

    @staticmethod
    def from_config(
        load_cfg: LoadConfig,
    ) -> pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection:
        """Get a Stac entity using information from load_cfg

        :param load_cfg: load information
        :type load_cfg: LoadConfig
        :return: pystac entity
        :rtype: pystac.Catalog | pystac.Collection | pystac.Item | pystac.ItemCollection
        """
        if load_cfg.json_location:
            return StacLoader._load_from_file(load_cfg.entity, load_cfg.json_location)
        return StacLoader._load_from_api(load_cfg.entity, cast(str, load_cfg.stac_api_endpoint))
