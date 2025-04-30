from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pystac

from stac_generator.core.base import (
    CollectionGenerator,
    ItemGenerator,
    StacCollectionConfig,
)
from stac_generator.core.base.schema import SourceConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.point import PointGenerator
from stac_generator.core.point.schema import PointConfig
from stac_generator.core.raster import RasterGenerator
from stac_generator.core.raster.schema import RasterConfig
from stac_generator.core.vector import VectorGenerator
from stac_generator.core.vector.schema import VectorConfig

if TYPE_CHECKING:
    from concurrent.futures import Executor

    import pystac


EXTENSION_MAP: dict[str, type[SourceConfig]] = {
    "csv": PointConfig,
    "txt": PointConfig,
    "geotiff": RasterConfig,
    "tiff": RasterConfig,
    "tif": RasterConfig,
    "zip": VectorConfig,
    "geojson": VectorConfig,
    "json": VectorConfig,
    "gpkg": VectorConfig,  # Can also contain raster data. TODO: overhaul interface
    "shp": VectorConfig,
}

CONFIG_GENERATOR_MAP: dict[type[SourceConfig], type[ItemGenerator]] = {
    VectorConfig: VectorGenerator,
    RasterConfig: RasterGenerator,
    PointConfig: PointGenerator,
}

BaseConfig_T = (
    str
    | Path
    | SourceConfig
    | dict[str, Any]
    | Sequence[str]
    | Sequence[SourceConfig]
    | Sequence[dict[str, Any]]
)
Config_T = BaseConfig_T | Sequence[BaseConfig_T]


class StacGeneratorFactory:
    @staticmethod
    def get_extension_handler(extension: str) -> type[SourceConfig]:
        """Match file extension with SourceConfig type"""
        if extension not in EXTENSION_MAP:
            raise ValueError(
                f"No SourceConfig matches extension: {extension}. Either change the extension or register a handler with the method `register_extension_handler`"
            )
        return EXTENSION_MAP[extension]

    @staticmethod
    def register_extension_handler(
        extension: str, handler: type[SourceConfig], force: bool = False
    ) -> None:
        """Dynamically register extension handler"""
        if extension in EXTENSION_MAP and not force:
            raise ValueError(
                f"Handler for extension: {extension} already exists: {EXTENSION_MAP[extension].__name__}. If this is intentional, use register_extension_handler with force=True"
            )
        if not issubclass(handler, SourceConfig):
            raise ValueError("Registered handler must be an instance of a subclass of SourceConfig")
        EXTENSION_MAP[extension] = handler

    @staticmethod
    def register_generator_handler(
        config: SourceConfig,
        handler: type[ItemGenerator],
        force: bool = False,
    ) -> None:
        """Dynamically register a customer ItemGenerator class based on (new/existing) config type. Use force to overwrite existing handler"""
        config_type = type(config)
        if config_type in CONFIG_GENERATOR_MAP and not force:
            raise ValueError(
                f"Handler for config: {config_type.__name__} already exists: {CONFIG_GENERATOR_MAP[config_type].__name__}. If this is intentional, use register_generator_handler with force=True"
            )
        if not issubclass(handler, ItemGenerator):
            raise ValueError(
                "Registered handler must be an instance of a subclass of ItemGenerator"
            )
        CONFIG_GENERATOR_MAP[config_type] = handler

    @staticmethod
    def get_generator_handler(config: SourceConfig) -> type[ItemGenerator]:
        """Match ItemGenrator class based on config type"""
        config_type = type(config)
        if config_type not in CONFIG_GENERATOR_MAP:
            raise ValueError(
                f"No ItemGenerator for config of type: {config_type.__name__}. To register a handler, use the method StacGeneratorFactor.register_generator_handler"
            )
        return CONFIG_GENERATOR_MAP[config_type]

    @staticmethod
    def extract_item_config(item: pystac.Item) -> SourceConfig:
        """Get stac_generator properties. Used by the MCCN engine"""
        if "stac_generator" not in item.properties:
            raise ValueError(f"Missing stac_generator properties for item: {item.id}")
        ext = item.properties["stac_generator"]["location"].split(".")[-1]
        handler = StacGeneratorFactory.get_extension_handler(ext)
        return handler.model_validate(item.properties["stac_generator"])

    @staticmethod
    def get_item_generators(  # noqa: C901
        configs: Config_T,
    ) -> list[ItemGenerator]:
        def handle_dict_config(config_dict: dict[str, Any]) -> SourceConfig:
            if "id" not in config_dict:
                raise ValueError("Missing id in a config item.")
            if "location" not in config_dict:
                raise ValueError(f"Missing location in a config item: {config_dict['id']}")
            ext = config_dict["location"].split(".")[-1]
            config_handler = StacGeneratorFactory.get_extension_handler(ext)
            return config_handler(**config_dict)

        def handle_str_config(config_str: str) -> list[SourceConfig]:
            configs = read_source_config(config_str)
            return [handle_dict_config(config) for config in configs]

        def handle_base_config(
            config: str | dict[str, Any] | SourceConfig | Path,
        ) -> list[SourceConfig]:
            configs: list[SourceConfig] = []
            if isinstance(config, str):
                configs.extend(handle_str_config(config))
            elif isinstance(config, Path):
                configs.extend(handle_str_config(config.as_posix()))
            elif isinstance(config, SourceConfig):
                configs.append(config)
            elif isinstance(config, dict):
                configs.append(handle_dict_config(config))
            else:
                raise TypeError(f"Invalid config item type: {type(config)}")
            return configs

        def handle_config(config: Config_T) -> list[SourceConfig]:
            if isinstance(config, str | dict | SourceConfig | Path):
                return handle_base_config(config)
            if hasattr(config, "__len__"):
                configs: list[SourceConfig] = []
                for item in config:
                    configs.extend(handle_config(item))
                return configs
            raise TypeError(f"Invalid config type: {type(config)}")

        parsed_configs = handle_config(configs)

        generators = []
        for config in parsed_configs:
            handler = StacGeneratorFactory.get_generator_handler(config)
            generators.append(handler(config))
        return generators

    @staticmethod
    def get_collection_generator(
        source_configs: Config_T,
        collection_config: StacCollectionConfig,
        pool: Executor | None = None,
    ) -> CollectionGenerator:
        """Get a CollectionGenerator instance based on source configs and
        collection config

        Args:
            source_configs (Config_T): extra metadata/generation parameters for
            the collection's items. Source configs can be given as:
            - a string path to a config.json file
            - a list of string paths to different config.json files
            - an instance of SourceConfig class (VectorConfig, PointConfig, RasterConfig), etc
            - a list of instances of SourceConfig.
            - a dictionary that follows the general structure of a SourceConfig class
            - a list of dictionaries
            If file paths are given, the files will be parsed into instances of SourceConfig.
            If dictionaries are given, they will be parsed into istances of SourceConfig using
            pydantic model_valiate.
            collection_config (StacCollectionConfig): collection metadata.
            pool (Executor | None): optional threadpool/process pool for parallel processing.

        Returns:
            CollectionGenerator: a collection generator instance, in which all items are derived
            from source _configs and general metadata derived from collection_config.
        """
        handlers = StacGeneratorFactory.get_item_generators(source_configs)
        return CollectionGenerator(collection_config, handlers, pool)
