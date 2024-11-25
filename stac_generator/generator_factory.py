import pandas as pd

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig
from stac_generator.csv.generator import CsvGenerator
from stac_generator.geotiff.generator import GeoTiffGenerator
from stac_generator.raster_data.generator import RasterGenerator
from stac_generator.vector_polygon.generator import VectorPolygonGenerator


class StacGeneratorFactory:
    @staticmethod
    def get_stac_generator(
        data_type: str,
        source_file: str,
        collection_cfg: StacCollectionConfig,
        catalog_cfg: StacCatalogConfig | None = None,
        href: str | None = None,
    ) -> StacGenerator:  # type: ignore[no-untyped-def]
        # Get the correct type of generator depending on the data type.
        source_df = pd.read_csv(source_file)

        if data_type == "geotiff":
            return GeoTiffGenerator(
                source_df,
                collection_cfg=collection_cfg,
                catalog_cfg=catalog_cfg,
                href=href,
            )
        if data_type == "csv":
            return CsvGenerator(
                source_df,
                collection_cfg=collection_cfg,
                catalog_cfg=catalog_cfg,
                href=href,
            )
        if data_type == "vector_polygon":
            return VectorPolygonGenerator(
                source_df,
                collection_cfg=collection_cfg,
                catalog_cfg=catalog_cfg,
                href=href,
            )
        if data_type == "raster":
            return RasterGenerator(
                source_df,
                collection_cfg=collection_cfg,
                catalog_cfg=catalog_cfg,
                href=href,
            )
        raise Exception(f"{data_type} is not a valid data type.")
