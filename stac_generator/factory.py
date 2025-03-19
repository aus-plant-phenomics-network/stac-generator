import collections
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Sequence, cast

import pandas as pd
from executing import Source

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


class StacGeneratorFactory:
    @staticmethod
    def match_handler(
        configs: Sequence[str | SourceConfig | dict[str, Any]],
    ) -> list[ItemGenerator]:
        # Read in configs
        _configs: list[dict[str, Any] | SourceConfig] = []
        for config in configs:
            if isinstance(config, str):
                _configs.extend(read_source_config(config))
            elif isinstance(config, dict | SourceConfig):
                _configs.append(config)
            else:
                raise TypeError(f"Invalid config item type: {type(config)}")
        handler_map: dict[type[ItemGenerator], dict[str, Any] | type[SourceConfig]] = (
            collections.defaultdict(list)  # type:ignore[arg-type]
        )
        for config in configs:
            if isinstance(config, dict):
                if "location" not in config:
                    raise ValueError("Missing location field in a config item.")
                ext = config["location"].split(".")[-1]
                ext_handler = StacGeneratorFactory.get_handler(ext)
                handler_map[ext_handler].append(config)
            else:
                ext_handler = CONFIG_GENERATOR_MAP[type(config)]
                handler_map[ext_handler].append(config)
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
    def get_stac_generator_from_files(
        source_configs: list[str], collection_config: StacCollectionConfig
    ) -> CollectionGenerator:
        handlers = StacGeneratorFactory.match_handler(source_configs)
        return CollectionGenerator(collection_config, handlers)

    @staticmethod
    def generate_config_template(
        source_configs: list[str],
        dst: str,
    ) -> None:
        # Determine config type based on file extension
        if dst.endswith(".json"):
            config_type = "json"
        elif dst.endswith(".csv"):
            config_type = "csv"
        else:
            raise ValueError("Expects csv or json template")
        # Match config type with corresponding handler
        handler_map = StacGeneratorFactory.match_handler(source_configs)
        result: list[Any] = []
        for k, v in handler_map.items():
            for item in v:
                if config_type == "json":
                    result.append(k.create_config(item))
                else:
                    result.append(pd.DataFrame([k.create_config(item)]))
        # Generate config template with pre-filled band/column info
        match config_type:
            case "json":
                with Path(dst).open("w") as file:
                    json.dump(result, file)
            case "csv":
                df = pd.concat(cast(Iterable[pd.DataFrame], result))
                if "column_info" in df.columns:
                    df["column_info"] = df["column_info"].apply(lambda item: json.dumps(item))
                if "band_info" in df.columns:
                    df["band_info"] = df["band_info"].apply(lambda item: json.dumps(item))
                df.to_csv(dst, index=False)
