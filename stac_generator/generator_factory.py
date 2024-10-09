import pandas as pd

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig
from stac_generator.csv.generator import CSVGenerator
from stac_generator.geotiff.generator import GeoTiffGenerator

__all__ = ("StacGeneratorFactory",)


class StacGeneratorFactory:
    @staticmethod
    def get_stac_generator(
        data_type: str,
        source_file: str,
        catalog_cfg: StacCatalogConfig | None = None,
    ) -> StacGenerator:  # type: ignore[no-untyped-def]
        # Get the correct type of generator depending on the data type.
        source_df = pd.read_csv(source_file)
        if data_type == "geotiff":
            return GeoTiffGenerator(source_df, catalog_cfg)
        if data_type == "csv":
            return CSVGenerator(source_df, catalog_cfg)
        raise Exception(f"{data_type} is not a valid data type.")
