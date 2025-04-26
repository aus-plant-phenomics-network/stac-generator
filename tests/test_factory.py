import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
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


@pytest.fixture(scope="module")
def composite_generator() -> CollectionGenerator:
    return StacGeneratorFactory.get_collection_generator(str(COMPOSITE_CONFIG), collection_config)


@pytest.fixture(scope="module")
def list_generator() -> CollectionGenerator:
    return StacGeneratorFactory.get_collection_generator(CONFIGS_LIST, collection_config)


@pytest.fixture(scope="module")
def threadpool_generator() -> Generator[CollectionGenerator, None, None]:
    executor = ThreadPoolExecutor(max_workers=4)
    # Use the executor to create a thread pool for the generator
    yield StacGeneratorFactory.get_collection_generator(
        CONFIGS_LIST,
        collection_config,
        pool=executor,
    )
    # Cleanup
    executor.shutdown(wait=True)


@pytest.mark.parametrize(
    "generator_fx",
    (
        "composite_generator",
        "list_generator",
        "threadpool_generator",
    ),
    ids=[
        "Composite Config",
        "List Configs",
        "ThreadPool Config",
    ],
)
def test_generator_factory(
    generator_fx: str,
    request: pytest.FixtureRequest,
) -> None:
    generator: CollectionGenerator = request.getfixturevalue(generator_fx)
    collection = generator()
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
