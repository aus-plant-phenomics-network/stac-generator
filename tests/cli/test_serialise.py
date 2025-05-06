import json
from pathlib import Path

import pytest
from pystac import Collection

from stac_generator.cli.serialise import serialise_handler
from tests.utils import compare_extent, compare_items


@pytest.mark.parametrize(
    "id,title,description,license,num_workers",
    [
        ("my_collection", "my_title", "my_description", "MIT", 1),
        ("my_collection", None, "my_description", "MIT", 4),
    ],
)
def test_serialise(
    id: str,
    title: str | None,
    description: str | None,
    license: str | None,
    num_workers: int,
    tmp_path: Path,
) -> None:
    dst = tmp_path / "generated"
    serialise_handler(
        id=id,
        src="tests/files/integration_tests/composite/config/composite_config.json",
        dst=dst.as_posix(),
        title=title,
        description=description,
        license=license,
        num_workers=num_workers,
    )
    generated_path = Path("tests/files/integration_tests/composite/generated")
    expected_collection_path = generated_path / "collection.json"
    with expected_collection_path.open() as file:
        expected_collection = json.load(file)

    actual_collection_path = dst / "collection.json"
    with actual_collection_path.open() as file:
        actual_collection = json.load(file)
    compare_extent(expected_collection, actual_collection)
    collection = Collection.from_file(actual_collection_path)
    assert collection.id == id
    assert collection.title == title
    assert collection.description == description
    assert collection.license == license
    for item in collection.get_items(recursive=True):
        config_loc = dst / f"{item.id}/{item.id}.json"
        with config_loc.open("r") as file:
            expected = json.load(file)
        actual = item.to_dict()
        compare_items(expected, actual)


@pytest.mark.parametrize("num_workers", [0, -1, -2])
def test_given_invalid_num_workers_expect_raises(num_workers: int) -> None:
    with pytest.raises(ValueError):
        serialise_handler(
            id="Collection",
            src="tests/files/integration_tests/composite/config/composite_config.json",
            dst="generated",
            title=None,
            description=None,
            license=None,
            num_workers=num_workers,
        )
