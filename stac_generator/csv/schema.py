from stac_generator.base.schema import SourceConfig
from stac_generator.typing import BandInfo


class CSVConfig(SourceConfig):
    X: str
    Y: str
    epgs: int
    T: str | None = None
    bands: list[str] | list[BandInfo] | None = None
    groupby: list[str] | None = None
    date_format: str = "ISO8601"
