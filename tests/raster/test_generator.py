import json
from pathlib import Path

import pytest

from stac_generator.base.generator import CollectionGenerator
from stac_generator.base.schema import StacCollectionConfig
from stac_generator.base.utils import read_source_config
from stac_generator.raster.generator import RasterGenerator
from stac_generator.raster.schema import RasterConfig

CONFIG_JSON = Path("tests/files/integration_tests/raster/config/raster_config.json")

CONFIG_CSV = Path("tests/files/integration_tests/raster/config/raster_config.csv")

GENERATED_DIR = Path("tests/files/integration_tests/raster/generated")


JSON_CONFIGS = read_source_config(str(CONFIG_JSON))
CSV_CONFIGS = read_source_config(str(CONFIG_CSV))
ITEM_IDS = [item["id"] for item in JSON_CONFIGS]


@pytest.fixture(scope="module")
def json_raster_generator() -> RasterGenerator:
    return RasterGenerator(JSON_CONFIGS)


@pytest.fixture(scope="module")
def csv_generator() -> RasterGenerator:
    return RasterGenerator(CSV_CONFIGS)


@pytest.fixture(scope="module")
def collection_generator(csv_generator: RasterGenerator) -> CollectionGenerator:
    return CollectionGenerator(StacCollectionConfig(id="raster_data"), generators=[csv_generator])


@pytest.mark.parametrize("item_idx", range(len(JSON_CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item(
    item_idx: int, json_raster_generator: RasterGenerator
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = json_raster_generator.create_item_from_config(RasterConfig(**config)).to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["geometry"] == actual["geometry"]
    assert expected["properties"] == actual["properties"]
    assert expected["assets"] == actual["assets"]


@pytest.mark.parametrize("item_idx", range(len(CSV_CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item_csv_config_version(
    item_idx: int, csv_generator: RasterGenerator
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = csv_generator.create_item_from_config(RasterConfig(**config)).to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["geometry"] == actual["geometry"]
    assert expected["properties"] == actual["properties"]
    assert expected["assets"] == actual["assets"]


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator.create_collection().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    assert actual["extent"] == expected["extent"]
