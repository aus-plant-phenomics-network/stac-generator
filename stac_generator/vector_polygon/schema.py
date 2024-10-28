from typing import Any
from pydantic import Field
from stac_generator.base.schema import SourceConfig

class VectorPolygonSourceConfig(SourceConfig):
    """Extended source config with EPSG code."""

    epsg: int = 4326 
    """EPSG code"""
