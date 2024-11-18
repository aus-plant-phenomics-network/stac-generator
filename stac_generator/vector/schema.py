from stac_generator.base.schema import SourceConfig


class VectorConfig(SourceConfig):
    """Extended source config with EPSG code."""

    epsg: int = 4326
    """EPSG code"""
