from stac_generator.base.schema import HasColumnInfo, SourceConfig


class VectorConfig(SourceConfig, HasColumnInfo):
    """Extended source config with EPSG code."""

    epsg: int = 4326
    """EPSG code for checking against EPSG code of the vector data"""
