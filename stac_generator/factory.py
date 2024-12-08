from typing import Any

from stac_generator.base import (
    CollectionGenerator,
    ItemGenerator,
    SourceConfig,
    StacCollectionConfig,
)
from stac_generator.base.utils import read_source_config
from stac_generator.point import PointGenerator
from stac_generator.raster import RasterGenerator
from stac_generator.vector import VectorGenerator

EXTENSION_MAP: dict[str, type[ItemGenerator]] = {
    "csv": PointGenerator,
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
        configs: list[dict[str, Any]] = []
        for source_config in source_configs:
            configs.extend(read_source_config(source_config))
        handler_map: dict[type[ItemGenerator], list[dict[str, Any]]] = {}
        for config in configs:
            base_config = SourceConfig(**config)
            if (
                handler := StacGeneratorFactory.get_handler(base_config.source_extension)
            ) in handler_map:
                handler_map[handler].append(config)
            else:
                handler_map[handler] = [config]
        handlers = [k(v) for k, v in handler_map.items()]
        return CollectionGenerator(collection_cfg, handlers)
