import datetime
import json
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

import pytest

from stac_generator.core.base import StacCollectionConfig
from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import SourceConfig
from stac_generator.core.point.schema import PointConfig
from stac_generator.core.vector import VectorGenerator
from stac_generator.core.vector.schema import VectorConfig
from stac_generator.factory import StacGeneratorFactory
from tests.utils import compare_extent, compare_items

FILE_PATH = Path("tests/files/integration_tests")
GENERATED_PATH = FILE_PATH / "composite/generated"
COLLECTION_ID = "collection"
collection_config = StacCollectionConfig(id=COLLECTION_ID)
CONFIGS_LIST = [
    str(FILE_PATH / "point/config/point_config.json"),
    str(FILE_PATH / "vector/config/vector_config.json"),
    str(FILE_PATH / "raster/config/raster_config.json"),
]
COMPOSITE_CONFIG = FILE_PATH / "composite/config/composite_config.json"


class DbfConfig(SourceConfig): ...


@pytest.fixture(scope="module")
def dbf_config() -> DbfConfig:
    return DbfConfig.model_validate(
        {
            "id": "item",
            "collection_date": "2020-01-01",
            "collection_time": "00:00",
            "location": "data.dbf",
        }
    )


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
    compare_extent(expected_collection, actual_collection)
    for item in collection.get_items(recursive=True):
        config_loc = GENERATED_PATH / f"{item.id}/{item.id}.json"
        with config_loc.open("r") as file:
            expected = json.load(file)
        actual = item.to_dict()
        compare_items(expected, actual)


@pytest.mark.parametrize(
    "config",
    [(123), (45.6), ([23, 4.5]), (None)],
)
def test_given_invalid_config_type_expects_raises(config: Any) -> None:
    with pytest.raises(TypeError):
        StacGeneratorFactory.get_item_generators(config)


@pytest.mark.parametrize(
    "config",
    [
        ({"id": "Missing Location"}),  # Missing Location
        ({"location": "data.csv"}),  # Missing ID
        (
            [{"id": "Full Item", "location": "data.geotiff"}, {"id": "Missing Location"}]
        ),  # Missing Location - list
        (
            [{"id": "Full Item", "location": "data.geotiff"}, {"location": "MissingID.csv"}]
        ),  # Missing ID - list
    ],
)
def test_given_dict_missing_id_location_expects_raises(
    config: dict[str, Any] | list[dict[str, Any]],
) -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.get_item_generators(config)


@pytest.mark.parametrize(
    "config",
    [
        # Raster config
        (
            {
                "id": "raster",
                "location": "data.geotiff",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
            },  # Raster - Missing BandInfo
        ),
        (
            {
                "id": "raster",
                "location": "data.geotiff",
                "collection_date": "2020-01-01",
                "band_info": [{"name": "red", "common_name": "red"}],
            },  # Raster - Missing collection time
        ),
        (
            {
                "id": "raster",
                "location": "data.geotiff",
                "collection_time": "00:00",
                "band_info": [{"name": "red", "common_name": "red"}],
            },  # Raster - Missing collection time
        ),
        (
            {
                "id": "raster",
                "location": "data.geotiff",
                "collection_date": "2025-01-05",
                "collection_time": "00:00",
                "band_info": [{"name": "red", "common_name": "red_ms"}],
            },  # Raster - invalid common name
        ),
        # Point config
        (
            {
                "id": "point",
                "location": "data.csv",
                "collection_time": "00:00",
                "X": "lat",
                "Y": "lon",
            },  # Point - missing date
        ),
        (
            {
                "id": "point",
                "location": "data.csv",
                "collection_date": "2020-01-01",
                "X": "lat",
                "Y": "lon",
            },  # Point - missing time
        ),
        (
            {
                "id": "point",
                "location": "data.csv",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "Y": "lon",
            },  # Point - missing X
        ),
        (
            {
                "id": "point",
                "location": "data.csv",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "X": "lat",
            },  # Point - missing Y
        ),
        # Vector config
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_time": "00:00",
            },  # vector missing date
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
            },  # vector missing time
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "name"}, {"name": "code"}],
                "join_config": {
                    "left_on": "name",
                    "right_on": "name",
                    "column_info": [{"name": "name"}, {"name": "area"}],
                },
            },  # vector join config - join config - missing file
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "name"}, {"name": "code"}],
                "join_config": {
                    "file": "join_file.csv",
                    "right_on": "name",
                    "column_info": [{"name": "name"}, {"name": "area"}],
                },
            },  # vector join config - join config - missing left on
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "name"}, {"name": "code"}],
                "join_config": {
                    "file": "join_file.csv",
                    "left_on": "name",
                    "column_info": [{"name": "name"}, {"name": "area"}],
                },
            },  # vector join config - join config - missing right on
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "name"}, {"name": "code"}],
                "join_config": {
                    "file": "join_file.csv",
                    "left_on": "name",
                    "right_on": "name",
                },
            },  # vector join config - join config - missing column info
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "code"}],
                "join_config": {
                    "file": "join_file.csv",
                    "left_on": "name",
                    "right_on": "name",
                    "column_info": [{"name": "name"}, {"name": "area"}],
                },
            },  # vector join config - join config - left on not in column info
        ),
        (
            {
                "id": "vector",
                "location": "data.geojson",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "column_info": [{"name": "name"}, {"name": "code"}],
                "join_config": {
                    "file": "join_file.csv",
                    "left_on": "name",
                    "right_on": "name",
                    "column_info": [{"name": "area"}],
                },
            },  # vector join config - join config - right on not in join column info
        ),
    ],
)
def test_given_dict_missing_important_fields_expects_raises(
    config: dict[str, Any] | list[dict[str, Any]],
) -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.get_item_generators(config)


def test_given_unregistered_config_ext_expects_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.get_extension_config_handler("dbf")


def test_given_unregistered_ext_expects_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.get_extension_handler("dbf")


def test_given_unregistered_config_class_expects_raises(dbf_config: DbfConfig) -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.get_generator_handler(dbf_config)


def test_given_registered_config_expects_no_error() -> None:
    StacGeneratorFactory.register_extension_handler("dbf", DbfConfig)
    assert StacGeneratorFactory.get_extension_handler("dbf") == DbfConfig


def test_given_registered_generator_expects_no_error(dbf_config: DbfConfig) -> None:
    StacGeneratorFactory.register_generator_handler(DbfConfig, VectorGenerator)
    assert StacGeneratorFactory.get_generator_handler(dbf_config) == VectorGenerator


def test_register_existing_ext_no_force_exp_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.register_extension_handler("csv", DbfConfig)


def test_register_invalid_handler_exp_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.register_extension_handler("dbf", VectorGenerator, force=True)  # type: ignore[arg-type]


def test_register_existing_ext_with_force_no_raises() -> None:
    StacGeneratorFactory.register_extension_handler("csv", DbfConfig, force=True)
    assert StacGeneratorFactory.get_extension_handler("csv") == DbfConfig


def test_register_existing_config_no_force_exp_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.register_generator_handler(PointConfig, VectorGenerator)


def test_register_existing_config_force_no_raises() -> None:
    StacGeneratorFactory.register_generator_handler(VectorConfig, VectorGenerator, force=True)
    assert (
        StacGeneratorFactory.get_generator_handler(
            VectorConfig(
                id="vector",
                collection_date=datetime.date(2020, 1, 1),
                collection_time=datetime.time(0, 0),
                location="data.geojson",
            )
        )
        == VectorGenerator
    )


def test_register_invalid_config_handler_exp_raises() -> None:
    with pytest.raises(ValueError):
        StacGeneratorFactory.register_generator_handler(VectorConfig, VectorConfig, force=True)  # type: ignore[arg-type]
