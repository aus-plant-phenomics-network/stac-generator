import json
import zipfile
from datetime import datetime

import fiona
import pandas as pd
import pystac
import pytest
from fiona.crs import from_epsg
from shapely.geometry import Polygon, mapping

from stac_generator.base.schema import SourceConfig, StacCollectionConfig
from stac_generator.vector_polygon.generator import VectorPolygonGenerator


@pytest.fixture
def create_sample_shapefile(tmpdir):
    """Create a sample shapefile inside a ZIP archive."""
    shapefile_dir = tmpdir.mkdir("shapefiles")
    shapefile_path = shapefile_dir.join("test_shapefile.shp")

    schema = {
        "geometry": "Polygon",
        "properties": {"id": "int"},
    }

    # Create a simple polygon feature
    polygon = Polygon([(-180, -90), (-180, 90), (180, 90), (180, -90), (-180, -90)])

    # Write to a shapefile using Fiona
    with fiona.open(
        str(shapefile_path), "w", driver="ESRI Shapefile", schema=schema, crs=from_epsg(4326)
    ) as layer:
        layer.write(
            {
                "geometry": mapping(polygon),
                "properties": {"id": 1},
            }
        )

    # Now create a ZIP archive for the shapefile
    zipfile_path = tmpdir.join("test_shapefile.zip")
    with zipfile.ZipFile(str(zipfile_path), "w") as z:
        for ext in [".shp", ".shx", ".dbf"]:
            z.write(str(shapefile_path).replace(".shp", ext), arcname=f"test_shapefile{ext}")

    return str(zipfile_path)


@pytest.fixture
def create_sample_geojson(tmpdir):
    """Create a sample GeoJSON file."""
    geojson_path = tmpdir.join("test_data.geojson")

    # Create a simple polygon feature
    polygon = Polygon([(-180, -90), (-180, 90), (180, 90), (180, -90), (-180, -90)])

    # Create a GeoJSON structure
    geojson_data = {
        "type": "FeatureCollection",
        "features": [{"type": "Feature", "geometry": mapping(polygon), "properties": {"id": 1}}],
    }

    # Write the GeoJSON data to a file
    with open(str(geojson_path), "w") as f:
        json.dump(geojson_data, f)

    return str(geojson_path)


@pytest.fixture
def vector_polygon_generator():
    collection_cfg = StacCollectionConfig(
        id="test_collection",
        title="Test Collection",
        description="Test description",
        license="CC-BY-4.0",
        extent=pystac.Extent(
            spatial=pystac.SpatialExtent([[-180, -90, 180, 90]]),
            temporal=pystac.TemporalExtent([[datetime.now(), None]]),
        ),
    )
    # Create a sample DataFrame
    sample_df = pd.DataFrame(
        {
            "id": ["test_vector"],
            "data_file": ["test.geojson"],
            "location_file": ["test.geojson"],
            "datetime": ["2023-01-01T00:00:00Z"],
            "properties": [{}],
            "prefix": ["test_prefix"],
            "location": ["http://example.com/test.geojson"],
        }
    )
    return VectorPolygonGenerator(source_df=sample_df, collection_cfg=collection_cfg)


def test_create_item_from_config_shapefile(vector_polygon_generator, create_sample_shapefile):
    source_config = SourceConfig(
        id="test_vector",
        data_file="test.shp",
        location_file="test.geojson",
        datetime="2023-01-01T00:00:00Z",
        properties={},
        prefix="test_prefix",
        location=create_sample_shapefile,
    )

    items = vector_polygon_generator.create_item_from_config(source_config)

    assert len(items) == 1
    item = items[0]
    assert item.id == "test_prefix"
    assert item.geometry is not None
    assert item.bbox == (-180.0, -90.0, 180.0, 90.0)
    assert "data" in item.assets
    assert item.assets["data"].href == create_sample_shapefile
    assert item.assets["data"].media_type == "application/x-shapefile"


def test_create_item_from_config_geojson(vector_polygon_generator, create_sample_geojson):
    source_config = SourceConfig(
        id="test_vector",
        data_file="test.geojson",
        location_file="test.geojson",
        datetime="2023-01-01T00:00:00Z",
        properties={},
        prefix="test_prefix",
        location=create_sample_geojson,
    )

    items = vector_polygon_generator.create_item_from_config(source_config)

    assert len(items) == 1
    item = items[0]
    assert item.id == "test_prefix"
    assert item.geometry is not None
    assert item.bbox == (-180.0, -90.0, 180.0, 90.0)
    assert "data" in item.assets
    assert item.assets["data"].href == create_sample_geojson
    assert item.assets["data"].media_type == pystac.MediaType.GEOJSON
