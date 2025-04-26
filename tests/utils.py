from typing import Any

import numpy as np


def compare_items(exp: dict[str, Any], ref: dict[str, Any]) -> None:
    assert exp["id"] == ref["id"]
    np.testing.assert_array_almost_equal(exp["bbox"], ref["bbox"])
    assert exp["geometry"].keys() == ref["geometry"].keys()
    assert exp["geometry"]["type"] == ref["geometry"]["type"]
    np.testing.assert_array_almost_equal(
        exp["geometry"]["coordinates"], ref["geometry"]["coordinates"]
    )
    assert exp["properties"] == ref["properties"]
    assert exp["assets"] == ref["assets"]


def compare_extent(exp: dict[str, Any], ref: dict[str, Any]) -> None:
    assert exp["extent"]["temporal"] == ref["extent"]["temporal"]
    np.testing.assert_array_almost_equal(
        exp["extent"]["spatial"]["bbox"], ref["extent"]["spatial"]["bbox"]
    )
