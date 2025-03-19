import collections
from collections.abc import Sequence
from typing import Any

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
    | SourceConfig
    | dict[str, Any]
    | Sequence[str]
    | Sequence[SourceConfig]
    | Sequence[dict[str, Any]]
)
Config_T = BaseConfig_T | Sequence[BaseConfig_T]


class StacGeneratorFactory:
    @staticmethod
    def match_handler(  # noqa: C901
        configs: Config_T,
    ) -> list[ItemGenerator]:
        # Read in configs
        _configs: list[SourceConfig] = []

        def handle_dict_config(config: dict[str, Any]) -> None:
            if "id" not in config:
                raise ValueError("Missing id in a config item.")
            if "location" not in config:
                raise ValueError(f"Missing location in a config item: {config['id']}")
            ext = config["location"].split(".")[-1]
            config_handler = StacGeneratorFactory.get_config_handler(ext)
            _configs.append(config_handler(**config))

        def handle_str_config(config: str) -> None:
            config_dicts = read_source_config(config)
            for item in config_dicts:
                handle_dict_config(item)

        def handle_source_config(config: SourceConfig) -> None:
            _configs.append(config)

        def handle_base_config(config: BaseConfig_T) -> None:
            if isinstance(config, str):
                handle_str_config(config)
            elif isinstance(config, SourceConfig):
                handle_source_config(config)
            elif isinstance(config, dict):
                handle_dict_config(config)
            else:
                raise TypeError(f"Invalid config item type: {type(config)}")

        def handle_config(config: Config_T) -> None:
            if isinstance(config, str | dict | SourceConfig):
                handle_base_config(config)
            elif hasattr(config, "__len__"):
                for item in config:
                    handle_config(item)
            else:
                raise TypeError(f"Invalid config type: {type(config)}")

        handle_config(configs)

        handler_map: dict[type[ItemGenerator], list[SourceConfig]] = collections.defaultdict(list)
        for config in _configs:
            generator_handler = StacGeneratorFactory.get_generator_handler(config)
            handler_map[generator_handler].append(config)

        generators = []
        for k, v in handler_map.items():
            generators.append(k(v))
        return generators

    @staticmethod
    def register_config_handler(
        extension: str, handler: type[SourceConfig], force: bool = False
    ) -> None:
        if extension in EXTENSION_MAP and not force:
            raise ValueError(
                f"Handler for extension: {extension} already exists: {EXTENSION_MAP[extension].__name__}. If this is intentional, use register_config_handler with force=True"
            )
        if not issubclass(handler, SourceConfig):
            raise ValueError("Registered handler must be an instance of a subclass of SourceConfig")
        EXTENSION_MAP[extension] = handler

    @staticmethod
    def register_generator_handler(
        config: SourceConfig, handler: type[ItemGenerator], force: bool = False
    ) -> None:
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
    def get_config_handler(extension: str) -> type[SourceConfig]:
        """Factory method to get SourceConfig class based on given extension

        :param extension: file extension
        :type extension: str
        :raises ValueError: if SourceConfig handler class for this file extension has not been registered_
        :return: handler class
        :rtype: type[SourceConfig]
        """
        if extension not in EXTENSION_MAP:
            raise ValueError(
                f"No SourceConfig matches extension: {extension}. Either change the extension or register a handler with the method `register_config_handler`"
            )
        return EXTENSION_MAP[extension]

    @staticmethod
    def get_generator_handler(config: SourceConfig) -> type[ItemGenerator]:
        config_type = type(config)
        if config_type not in CONFIG_GENERATOR_MAP:
            raise ValueError(
                f"No ItemGenerator for config of type: {config_type.__name__}. To register a handler, use the method StacGeneratorFactor.register_generator_handler"
            )
        return CONFIG_GENERATOR_MAP[config_type]

    @staticmethod
    def get_stac_generator(
        source_configs: Config_T, collection_config: StacCollectionConfig
    ) -> CollectionGenerator:
        handlers = StacGeneratorFactory.match_handler(source_configs)
        return CollectionGenerator(collection_config, handlers)
