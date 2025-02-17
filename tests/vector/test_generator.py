import json
from pathlib import Path

import pytest

from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.vector.generator import VectorGenerator
from stac_generator.core.vector.schema import VectorConfig

CONFIG_JSON = Path("tests/files/integration_tests/vector/config/vector_config.json")

CONFIG_CSV = Path("tests/files/integration_tests/vector/config/vector_config.csv")

GENERATED_DIR = Path("tests/files/integration_tests/vector/generated")


JSON_CONFIGS = read_source_config(str(CONFIG_JSON))
CSV_CONFIGS = read_source_config(str(CONFIG_CSV))
ITEM_IDS = [item["id"] for item in JSON_CONFIGS]


@pytest.fixture(scope="module")
def json_vector_generator() -> VectorGenerator:
    return VectorGenerator(JSON_CONFIGS)


@pytest.fixture(scope="module")
def vector_generator() -> VectorGenerator:
    return VectorGenerator(CSV_CONFIGS)


@pytest.fixture(scope="module")
def collection_generator(vector_generator: VectorGenerator) -> CollectionGenerator:
    return CollectionGenerator(
        StacCollectionConfig(id="vector_data"), generators=[vector_generator]
    )


@pytest.mark.parametrize("item_idx", range(len(JSON_CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item(
    item_idx: int, json_vector_generator: VectorGenerator
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = json_vector_generator.create_item_from_config(VectorConfig(**config)).to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["properties"] == actual["properties"]
    assert expected["assets"] == actual["assets"]
    assert expected["geometry"] == actual["geometry"]


@pytest.mark.parametrize("item_idx", range(len(CSV_CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item_csv_config_version(
    item_idx: int, vector_generator: VectorGenerator
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = vector_generator.create_item_from_config(VectorConfig(**config)).to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["properties"] == actual["properties"]
    assert expected["assets"] == actual["assets"]
    assert expected["geometry"] == actual["geometry"]


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator.create_collection().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    assert actual["extent"] == expected["extent"]
