import urllib.parse

import httpx
import pytest

from stac_generator.base import CollectionGenerator, StacCollectionConfig
from stac_generator.base.utils import read_source_config
from stac_generator.vector import VectorConfig, VectorGenerator
from tests import REMOTE_FIXTURE_URL

JSON_CONFIG_PATH = urllib.parse.urljoin(
    str(REMOTE_FIXTURE_URL), "unit_tests/vector/config/vector_config.json"
)


REMOTE_GENERATED_DIR = urllib.parse.urljoin(
    str(REMOTE_FIXTURE_URL), "unit_tests/vector/generated_stac/"
)


JSON_CONFIGS = read_source_config(JSON_CONFIG_PATH)
ITEM_IDS = [item["id"] for item in JSON_CONFIGS]


@pytest.fixture(scope="module")
def json_vector_generator() -> VectorGenerator:
    return VectorGenerator(JSON_CONFIGS)


@pytest.fixture(scope="module")
def collection_generator(json_vector_generator: VectorGenerator) -> CollectionGenerator:
    return CollectionGenerator(
        StacCollectionConfig(id="vector"), generators=[json_vector_generator]
    )


@pytest.mark.parametrize(
    "item_idx",
    range(len(JSON_CONFIGS)),
    ids=ITEM_IDS,
)
def test_generator_given_item_expects_matched_generated_item(
    item_idx: int, json_vector_generator: VectorGenerator
) -> None:
    config = JSON_CONFIGS[item_idx]
    expected_path = urllib.parse.urljoin(REMOTE_GENERATED_DIR, f"{config['id']}.json")
    data = httpx.get(expected_path)
    expected = data.json()
    actual = json_vector_generator.create_item_from_config(VectorConfig(**config)).to_dict()
    assert expected["id"] == actual["id"]
    assert expected["bbox"] == actual["bbox"]
    assert expected["properties"] == actual["properties"]
    assert expected["assets"] == actual["assets"]
    assert expected["geometry"] == actual["geometry"]


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator.create_collection().to_dict()
    expected_path = urllib.parse.urljoin(REMOTE_GENERATED_DIR, "collection.json")
    data = httpx.get(expected_path)
    expected = data.json()
    assert actual["extent"] == expected["extent"]
