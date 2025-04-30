import datetime
import json
from pathlib import Path

import pytest

from stac_generator.core.base.generator import CollectionGenerator
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.core.base.utils import read_source_config
from stac_generator.core.raster.generator import RasterGenerator
from stac_generator.core.raster.schema import BandInfo, RasterConfig
from stac_generator.exceptions import SourceAssetException
from tests.utils import compare_extent, compare_items

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
    compare_items(expected, actual)


def test_collection_generator(collection_generator: CollectionGenerator) -> None:
    actual = collection_generator().to_dict()
    expected_path = GENERATED_DIR / "collection.json"
    with expected_path.open() as file:
        expected = json.load(file)
    compare_extent(expected, actual)


def test_given_non_existent_location_expects_raise_SourceAssetException() -> None:
    ts = datetime.datetime.now()
    config = RasterConfig(
        id="item",
        location="non_existent.tif",
        collection_date=ts.date(),
        collection_time=ts.time(),
        band_info=[BandInfo(name="Invalid_Band")],
    )
    item_generator = RasterGenerator(config)
    with pytest.raises(SourceAssetException):
        item_generator.generate()


def test_given_no_band_info_expects_raises() -> None:
    with pytest.raises(ValueError):
        RasterConfig.model_validate(
            {
                "id": "item",
                "location": "non_existent.tif",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
            }
        )


def test_given_invalid_common_name_expects_raises() -> None:
    with pytest.raises(ValueError):
        RasterConfig.model_validate(
            {
                "id": "item",
                "location": "non_existent.tif",
                "collection_date": "2020-01-01",
                "collection_time": "00:00",
                "band_info": [{"name": "band1", "common_name": "band1"}],
            }
        )


def test_given_valid_common_name_capital_expects_lowered() -> None:
    config = RasterConfig.model_validate(
        {
            "id": "item",
            "location": "non_existent.tif",
            "collection_date": "2020-01-01",
            "collection_time": "00:00",
            "band_info": [{"name": "RED", "common_name": "RED"}],
        }
    )
    assert config.band_info[0].name == "red"
    assert config.band_info[0].common_name == "red"


def test_given_valid_pathlibPath_expects_correct_serialisation() -> None:
    ts = datetime.datetime.now()
    config = RasterConfig(
        id="time",
        location=Path("/path/to/file.tif"),  # type: ignore[arg-type]
        collection_date=ts.date(),
        collection_time=ts.time(),
        band_info=[BandInfo(name="Invalid_Band")],
    )
    assert config.location == "/path/to/file.tif"


def test_given_invalid_path_type_expects_raises() -> None:
    with pytest.raises(ValueError):
        ts = datetime.datetime.now()
        RasterConfig(
            id="time",
            location=123,  # type: ignore[arg-type]
            collection_date=ts.date(),
            collection_time=ts.time(),
            band_info=[BandInfo(name="Invalid_Band")],
        )
