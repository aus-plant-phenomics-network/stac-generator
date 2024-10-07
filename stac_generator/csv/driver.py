from typing import Any

from stac_generator.base.driver import IODriver
from stac_generator.csv.schema import CSVConfig
from stac_generator.csv.utils import read_csv, to_gdf
from stac_generator.typing import FrameT, PDFrameT


class CSVDriver(IODriver):
    def __init__(self, config: CSVConfig) -> None:
        super().__init__(config)
        self.config: CSVConfig

    def get_data(self) -> FrameT:
        return self.read_local()

    def to_gdf(self, df: PDFrameT) -> FrameT:
        return to_gdf(df, self.config.X, self.config.Y, self.config.epgs)

    def read_local(self) -> FrameT:
        assert self.config.local is not None
        df = read_csv(
            self.config.local,
            self.config.X,
            self.config.Y,
            self.config.T,
            self.config.date_format,
            self.config.bands,
            self.config.groupby,
        )
        return self.to_gdf(df)
