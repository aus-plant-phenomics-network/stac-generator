import collections
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any, cast

import pandas as pd

from stac_generator.core.base import (
    CollectionGenerator,
    ItemGenerator,
    SourceConfig,
    StacCollectionConfig,
)
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.point import PointGenerator
from stac_generator.core.raster import RasterGenerator
from stac_generator.core.vector import VectorGenerator

EXTENSION_MAP: dict[str, type[ItemGenerator]] = {
    "csv": PointGenerator,
    "txt": PointGenerator,
    "geotiff": RasterGenerator,
    "tiff": RasterGenerator,
    "tif": RasterGenerator,
    "zip": VectorGenerator,
    "geojson": VectorGenerator,
    "json": VectorGenerator,
    "gpkg": VectorGenerator,  # Can also contain raster data. TODO: overhaul interface
    "shp": VectorGenerator,
}


class StacGeneratorFactory:
    @staticmethod
    def register_handler(extension: str, handler: type[ItemGenerator], force: bool = False) -> None:
        if extension in EXTENSION_MAP and not force:
            raise ValueError(
                f"Handler for extension: {extension} already exists: {EXTENSION_MAP[extension]}. If this is intentional, use register_handler with force=True"
            )
        if not issubclass(handler, ItemGenerator):
            raise ValueError(
                "Registered handler must be an instance of a subclass of ItemGenerator"
            )
        EXTENSION_MAP[extension] = handler

    @staticmethod
    def get_handler(extension: str) -> type[ItemGenerator]:
        """Factory method to get ItemGenerator class based on given extension

        :param extension: file extension
        :type extension: str
        :raises ValueError: if ItemGenerator handler class for this file extension has not been registered_
        :return: handler class
        :rtype: type[ItemGenerator]
        """
        if extension not in EXTENSION_MAP:
            raise ValueError(
                f"No ItemGenerator matches extension: {extension}. Either change the extension or register a handler with the method `register_handler`"
            )
        return EXTENSION_MAP[extension]

    @staticmethod
    def get_stac_generator(
        source_configs: list[str], collection_cfg: StacCollectionConfig
    ) -> CollectionGenerator:
        handler_map = StacGeneratorFactory.match_handler(source_configs)
        handlers = [k(v) for k, v in handler_map.items()]
        return CollectionGenerator(collection_cfg, handlers)

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

    @staticmethod
    def match_handler(source_configs: list[str]) -> dict[type[ItemGenerator], list[dict[str, Any]]]:
        configs: list[dict[str, Any]] = []
        for source_config in source_configs:
            configs.extend(read_source_config(source_config))
        handler_map: dict[type[ItemGenerator], list[dict[str, Any]]] = collections.defaultdict(list)
        for config in configs:
            base_config = SourceConfig(**config)
            handler = StacGeneratorFactory.get_handler(base_config.source_extension)
            handler_map[handler].append(config)
        return handler_map
