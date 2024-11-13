from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING, Any, Generic

import pystac
from pystac.collection import Extent

from stac_generator.base.schema import (
    StacCollectionConfig,
    T,
)
from stac_generator.base.utils import (
    extract_spatial_extent,
    extract_temporal_extent,
    force_write_to_stac_api,
    href_is_stac_api_endpoint,
    parse_href,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


class CollectionGenerator:
    """CollectionGenerator class. User should not need to subclass this class unless greater control over how collection is generated from items is needed."""

    def __init__(
        self,
        collection_cfg: StacCollectionConfig,
        generators: Sequence[ItemGenerator],
    ) -> None:
        """CollectionGenerator - generate collection from generators attribute

        :param collection_cfg: collection metadata
        :type collection_cfg: StacCollectionConfig
        :param generators: sequence of ItemGenerator subclasses.
        :type generators: Sequence[ItemGenerator]
        """
        self.collection_cfg = collection_cfg
        self.generators = generators

    def _create_collection_from_items(
        self,
        items: list[pystac.Item],
        collection_cfg: StacCollectionConfig | None = None,
    ) -> pystac.Collection:
        logger.debug("generating collection from items")
        if collection_cfg is None:
            raise ValueError("Generating collection requires non null collection config")
        collection = pystac.Collection(
            id=collection_cfg.id,
            description=(
                collection_cfg.description
                if collection_cfg.description
                else f"Auto-generated collection {collection_cfg.id} with stac_generator"
            ),
            extent=Extent(extract_spatial_extent(items), extract_temporal_extent(items)),
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

    def create_collection(self) -> pystac.Collection:
        """Generate collection from all gathered items

        Spatial extent is the bounding box enclosing all items
        Temporal extent is the time interval enclosing temporal extent of all items. Note that this value is automatically calculated
        and provided temporal extent fields (start_datetime, end_datetime) at collection level will be ignored

        :return: generated collection
        :rtype: pystac.Collection
        """
        items = []
        for generator in self.generators:
            items.extend(generator.create_items())
        return self._create_collection_from_items(items, self.collection_cfg)


class ItemGenerator(abc.ABC, Generic[T]):
    """Base ItemGenerator object. Users should extend this class for handling different file extensions."""

    source_type: type[T]
    """SourceConfig subclass that contains information used for parsing the source file"""

    @classmethod
    def __class_getitem__(cls, source_type: type) -> type:
        kwargs = {"source_type": source_type}
        return type(f"ItemGenerator[{source_type.__name__}]", (ItemGenerator,), kwargs)

    def __init__(
        self,
        configs: list[dict[str, Any]],
    ) -> None:
        """Base ItemGenerator object. Users should extend this class for handling different file extensions.

        :param configs: source data configs - either from csv config or yaml/json
        :type configs: list[dict[str, Any]]
        """
        logger.debug("validating config")
        self.configs = [self.source_type(**config) for config in configs]

    @abc.abstractmethod
    def create_item_from_config(self, source_cfg: T) -> pystac.Item:
        """Abstract method that handles `pystac.Item` generation from the appropriate config"""
        raise NotImplementedError

    def create_items(self) -> list[pystac.Item]:
        """Generate STAC Items from `configs` metadata

        :return: list of generated STAC Item
        :rtype: list[pystac.Item]
        """
        logger.debug(f"generating items using {self.__class__.__name__}")
        items = []
        for config in self.configs:
            items.append(self.create_item_from_config(config))
        return items


class StacSerialiser:
    def __init__(self, generator: CollectionGenerator, href: str) -> None:
        self.generator = generator
        self.collection = generator.create_collection()
        self.href = href
        StacSerialiser.pre_serialisation_hook(self.collection, self.href)

    @staticmethod
    def pre_serialisation_hook(collection: pystac.Collection, href: str) -> None:
        """Hook that can be overwritten to provide pre-serialisation functionality.
        By default, this normalises collection href and performs validation

        :param collection: collection object
        :type collection: pystac.Collection
        :param href: serialisation href
        :type href: str
        """
        logger.debug("validating generated collection and items")
        collection.normalize_hrefs(href)
        collection.validate_all()

    def __call__(self) -> None:
        if href_is_stac_api_endpoint(self.href):
            return self.to_json()
        return self.to_api()

    def to_json(self) -> None:
        """Generate STAC Collection and save to disk as json files"""
        logger.debug("saving collection as local json")
        self.collection.save()
        logger.info(f"successfully save collection to {self.href}")

    def to_api(self) -> None:
        """_Generate STAC Collection and push to remote API.
        The API will first attempt to send a POST request which will be replaced with a PUT request if a 409 error is encountered
        """
        logger.debug("save collection to STAC API")
        force_write_to_stac_api(
            url=parse_href(self.href, f"collections/{self.collection.id}"),
            json=self.collection.to_dict(),
        )
        for item in self.collection.get_all_items():
            force_write_to_stac_api(
                url=parse_href(self.href, f"collections/{self.collection.id}/items/{item.id}"),
                json=item.to_dict(),
            )
        logger.info(f"successfully save collection to {self.href}")
