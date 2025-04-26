import json
from pathlib import Path

import pytest

from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.raster.generator import RasterGenerator
from tests.utils import compare_dict_except

CONFIG_JSON = Path("tests/files/integration_tests/raster/config/raster_config.json")


GENERATED_DIR = Path("tests/files/integration_tests/raster/generated")


JSON_CONFIGS = read_source_config(str(CONFIG_JSON))
ITEM_IDS = [item["id"] for item in JSON_CONFIGS]


@pytest.fixture(scope="module")
def raster_generators() -> list[RasterGenerator]:
    return [RasterGenerator(config) for config in JSON_CONFIGS]


@pytest.fixture(scope="module")
def collection_generator(raster_generators: list[RasterGenerator]) -> CollectionGenerator:
    return CollectionGenerator(StacCollectionConfig(id="collection"), generators=raster_generators)


@pytest.mark.parametrize("item_idx", range(len(JSON_CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item(
    item_idx: int, raster_generators: list[RasterGenerator]
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = raster_generators[item_idx].generate().to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["geometry"] == actual["geometry"]
    compare_dict_except(expected["properties"], actual["properties"])
    assert expected["assets"] == actual["assets"]


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    assert actual["extent"] == expected["extent"]
