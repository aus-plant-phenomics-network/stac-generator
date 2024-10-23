import json
import zipfile
from pathlib import Path

import fiona
import pystac
import pytest
from fiona.crs import from_epsg
from shapely.geometry import Polygon, mapping

from stac_generator.vector_polygon_stac_generator import VectorPolygonStacGenerator


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
def stac_generator(create_sample_shapefile, create_sample_geojson):
    """Fixture to initialize the STAC generator."""
    data_file = create_sample_shapefile
    location_file = create_sample_geojson

    return VectorPolygonStacGenerator(data_file=data_file, location_file=location_file)


def test_output_directory_exists(stac_generator):
    """Test that the output directory is created."""
    output_dir = Path("./tests/stac")
    assert output_dir.exists(), "Output directory should exist."
    assert output_dir.is_dir(), "Output directory should be a directory."


def test_generate_item(stac_generator):
    """Test that STAC items are generated correctly."""
    assert len(stac_generator.items) == 2, "Two STAC items should be generated."

    for item in stac_generator.items:
        assert isinstance(item, pystac.Item), "Generated object should be a STAC Item."
        assert item.id is not None, "Item should have an ID."
        assert item.geometry is not None, "Item should have geometry."
        assert item.bbox is not None, "Item should have a bounding box."

        # Convert the actual bbox to a list before comparison
        actual_bbox = list(item.bbox)

        # Check if the bounding box matches the expected value
        expected_bbox = [-180.0, -90.0, 180.0, 90.0]
        assert (
            actual_bbox == expected_bbox
        ), f"Expected bbox: {expected_bbox}, but got: {actual_bbox}"

        # Use pytest.approx to compare the coordinates list more flexibly
        expected_coords = [[-180, -90], [-180, 90], [180, 90], [180, -90], [-180, -90]]
        for actual_coord, expected_coord in zip(item.geometry["coordinates"][0], expected_coords):
            assert (
                pytest.approx(actual_coord, rel=1e-9) == expected_coord
            ), f"Expected coord: {expected_coord}, but got: {actual_coord}"


def test_generate_collection(stac_generator):
    """Test that a STAC collection is generated correctly."""
    collection = stac_generator.generate_collection()

    assert isinstance(
        collection, pystac.Collection
    ), "Generated object should be a STAC Collection."
    assert collection.id == "vector_collection", "Collection ID should be set correctly."
    assert collection.extent is not None, "Collection should have an extent."

    # Convert chain object to a list before checking length
    items_list = list(collection.get_all_items())
    assert len(items_list) == 2, "Collection should contain two items."

    # Check if the collection's spatial extent is correct
    expected_bbox = [-180, -90, 180, 90]
    collection_bbox = collection.extent.spatial.bboxes[0]
    assert (
        collection_bbox == expected_bbox
    ), f"Expected bbox: {expected_bbox}, but got: {collection_bbox}"


def test_generate_catalog(stac_generator):
    """Test that a STAC catalog is generated correctly."""
    catalog = stac_generator.generate_catalog()

    assert isinstance(catalog, pystac.Catalog), "Generated object should be a STAC Catalog."
    assert catalog.id == "vector_catalog", "Catalog ID should be set correctly."

    # Convert chain object to a list before checking length
    items_list = list(catalog.get_all_items())
    assert len(items_list) == 2, "Catalog should contain two items."


def test_validate_stac(stac_generator):
    """Test the STAC validation process."""
    assert stac_generator.validate_stac(), "STAC validation should pass."


def test_normalize_hrefs(stac_generator):
    """Test that hrefs are normalized correctly."""
    try:
        stac_generator.generate_collection()  # Normalize hrefs inside generate_collection
        for item in stac_generator.collection.get_all_items():
            assert item.get_self_href() is not None, "Each item should have a self href."
        assert True  # If no exceptions were raised, the test passes
    except Exception as e:
        pytest.fail(f"normalize_hrefs raised an exception: {e!s}")
