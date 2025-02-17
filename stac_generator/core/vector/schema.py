from stac_generator.core.base.schema import HasColumnInfo, SourceConfig


class VectorConfig(SourceConfig, HasColumnInfo):
    """Extended source config with EPSG code."""

    epsg: int | None = None
    """EPSG code for checking against EPSG code of the vector data"""

    layer: str | None = None
    """Vector layer for multi-layer shapefile"""
