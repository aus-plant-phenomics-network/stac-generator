import json
from pathlib import Path

import pytest

from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.vector.generator import VectorGenerator
from tests.utils import compare_dict_except

CONFIG_JSON = Path("tests/files/integration_tests/vector/config/vector_config.json")


GENERATED_DIR = Path("tests/files/integration_tests/vector/generated")


CONFIGS = read_source_config(str(CONFIG_JSON))
ITEM_IDS = [item["id"] for item in CONFIGS]


@pytest.fixture(scope="module")
def vector_generators() -> list[VectorGenerator]:
    return [VectorGenerator(config) for config in CONFIGS]


@pytest.fixture(scope="module")
def collection_generator(vector_generators: list[VectorGenerator]) -> CollectionGenerator:
    return CollectionGenerator(StacCollectionConfig(id="collection"), generators=vector_generators)


@pytest.mark.parametrize("item_idx", range(len(CONFIGS)), ids=ITEM_IDS)
def test_generator_given_item_expects_matched_generated_item(
    item_idx: int, vector_generators: list[VectorGenerator]
) -> None:
    config = CONFIGS[item_idx]
    expected_path = GENERATED_DIR / f"{config['id']}/{config['id']}.json"
    with expected_path.open() as file:
        expected = json.load(file)
    actual = vector_generators[item_idx].generate().to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    compare_dict_except(expected["properties"], actual["properties"])
    assert expected["assets"] == actual["assets"]
    assert expected["geometry"] == actual["geometry"]


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    assert actual["extent"] == expected["extent"]
