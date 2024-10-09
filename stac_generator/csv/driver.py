import geopandas as gpd
import pandas as pd

from stac_generator.base.driver import IODriver
from stac_generator.csv.schema import CsvConfig
from stac_generator.csv.utils import read_csv, to_gdf


class CsvDriver(IODriver):
    def __init__(self, config: CsvConfig) -> None:
        super().__init__(config)
        self.config: CsvConfig

    def get_data(self) -> gpd.GeoDataFrame:
        return self.read_local()

    def _to_gdf(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        return to_gdf(df, self.config.X, self.config.Y, self.config.epsg)

    def read_local(self) -> gpd.GeoDataFrame:
        assert self.config.local is not None
        df = read_csv(
            self.config.local,
            self.config.X,
            self.config.Y,
            self.config.T,
            self.config.date_format,
            self.config.column_info,
            self.config.groupby,
        )
        return self._to_gdf(df)
