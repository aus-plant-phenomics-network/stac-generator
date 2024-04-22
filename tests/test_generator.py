import json
from pathlib import Path

from stac_generator.drone_stac_generator import DroneStacGenerator
from stac_generator.generator_factory import StacGeneratorFactory


def test_generator() -> None:
    data_file = Path("tests/test_data/drone_test.csv")
    data_type = data_file.stem.split("_")[0]
    assert data_type == "drone"
    location_file = Path("tests/test_data/drone_test_files.csv")
    # Create the STAC catalog
    generator = StacGeneratorFactory().get_stac_generator(data_type, data_file,
                                                          location_file)
    assert isinstance(generator, DroneStacGenerator)
    assert generator.validate_stac()
    # Checks for the collection
    assert generator.collection
    actual_col = generator.collection.to_dict()
    expected_col_file = Path("tests/test_data/expected_collection.json")
    with open(expected_col_file, 'r') as f:
        expected_col = json.load(f)
    assert actual_col == expected_col
    # Checks for items.
    actual_item = generator.items[0].to_dict()
    # Check all the expected extensions have been recorded.
    assert len(actual_item["stac_extensions"]) == 3
    expected_extensions = [
        "https://stac-extensions.github.io/projection/v1.1.0/schema.json",
        "https://stac-extensions.github.io/eo/v1.1.0/schema.json",
        "https://stac-extensions.github.io/raster/v1.1.0/schema.json"
    ]
    assert actual_item["stac_extensions"] == expected_extensions
    # Check the expected keys are at the 'properties' level.
    expected_keys = ["eo:bands", "proj:epsg", "proj:shape", "eo:snow_cover", "eo:cloud_cover",
                     "proj:transform"]
    actual_keys = actual_item["properties"].keys()
    for expected_key in expected_keys:
        assert expected_key in actual_keys
    # Check the expected keys are at the 'assets' level.
    expected_keys = ["eo:bands", "raster:bands"]
    actual_keys = actual_item["assets"]["image"].keys()
    for expected_key in expected_keys:
        assert expected_key in actual_keys
