import json
from pathlib import Path

import pytest

from stac_generator.core.base import StacCollectionConfig
from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.factory import StacGeneratorFactory
from tests.utils import compare_dict_except

FILE_PATH = Path("tests/files/integration_tests")
GENERATED_PATH = FILE_PATH / "composite/generated"
COLLECTION_ID = "collection"
collection_config = StacCollectionConfig(id=COLLECTION_ID)
CONFIGS_LIST = [
    str(FILE_PATH / "point/config/point_config.csv"),
    str(FILE_PATH / "vector/config/vector_config.json"),
    str(FILE_PATH / "raster/config/raster_config.csv"),
]
COMPOSITE_CONFIG = FILE_PATH / "composite/config/composite_config.json"


# One single config that is a composition of multiple configs
composite_generator = StacGeneratorFactory.get_stac_generator(
    [str(COMPOSITE_CONFIG)], collection_config
)
# Config provided as a list of configs
list_generator = StacGeneratorFactory.get_stac_generator(CONFIGS_LIST, collection_config)


@pytest.mark.parametrize(
    "generator",
    (composite_generator, list_generator),
    ids=["Composite Config", "List Configs"],
)
def test_generator_factory(
    generator: CollectionGenerator,
) -> None:
    collection = generator.create_collection()
    expected_collection_path = GENERATED_PATH / "collection.json"
    with expected_collection_path.open() as file:
        expected_collection = json.load(file)
    actual_collection = collection.to_dict()
    assert actual_collection["extent"] == expected_collection["extent"]
    for item in collection.get_items(recursive=True):
        config_loc = GENERATED_PATH / f"{item.id}/{item.id}.json"
        with config_loc.open("r") as file:
            expected = json.load(file)
        actual = item.to_dict()
        assert expected["id"] == actual["id"]
        assert expected["bbox"] == actual["bbox"]
        assert expected["geometry"] == actual["geometry"]
        compare_dict_except(expected["properties"], actual["properties"])
        assert expected["assets"] == actual["assets"]
