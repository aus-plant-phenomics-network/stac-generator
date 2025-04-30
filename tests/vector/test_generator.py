import datetime
import json
from pathlib import Path

import pytest

from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.vector.generator import VectorGenerator
from stac_generator.core.vector.schema import JoinConfig, VectorConfig
from stac_generator.exceptions import SourceAssetException
from tests.utils import compare_extent, compare_items

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
    compare_items(expected, actual)


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    compare_extent(expected, actual)


def test_given_non_existent_join_location_expects_raise_SourceAssetException() -> None:
    config = {
        "id": "valid_vector",
        "location": "tests/files/unit_tests/vectors/Werribee.geojson",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "column_info": [{"name": "Suburb_Name", "description": "Suburb_Name"}],
        "join_config": {
            "file": "Non-Existent.csv",
            "left_on": "Suburb_Name",
            "right_on": "Area",
            "column_info": [
                {"name": "Area", "description": "Area name"},
                {"name": "Distance", "description": "Driving Distance to CBD in km"},
                {
                    "name": "Public_Transport",
                    "description": "Time taken to reach CBD by public transport in minutes",
                },
                {"name": "Drive", "description": "Time taken to reach CBD by driving in minutes"},
                {"name": "Growth", "description": "Average 5 year growth in percentage in 2025"},
                {"name": "Yield", "description": "Average rental yield in 2025"},
            ],
        },
    }
    item_generator = VectorGenerator(config)
    with pytest.raises(SourceAssetException):
        item_generator.generate()


def test_given_non_existent_location_expects_raise_SourceAssetException() -> None:
    ts = datetime.datetime.now()
    config = VectorConfig(
        id="item",
        location="non_existent.shp",
        collection_date=ts.date(),
        collection_time=ts.time(),
    )
    item_generator = VectorGenerator(config)
    with pytest.raises(SourceAssetException):
        item_generator.generate()


def test_given_empty_join_column_info_expects_raises() -> None:
    with pytest.raises(ValueError):
        JoinConfig.model_validate(
            {
                "file": "non_existent.csv",
                "left_on": "column",
                "right_on": "column",
                "column_info": [],
            }
        )
