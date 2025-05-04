from pathlib import Path
from typing import Any

import numpy as np


def compare_assets(exp: dict[str, Any], ref: dict[str, Any]) -> None:
    assert exp.keys() == ref.keys()
    for k in exp.keys():
        if k != "href":
            assert exp[k] == ref[k]
        else:
            exp_p = Path(exp[k])
            ref_p = Path(ref[k])
            assert exp_p == ref_p


def compare_items(exp: dict[str, Any], ref: dict[str, Any]) -> None:
    assert exp["id"] == ref["id"]
    np.testing.assert_array_almost_equal(exp["bbox"], ref["bbox"])
    assert exp["geometry"].keys() == ref["geometry"].keys()
    assert exp["geometry"]["type"] == ref["geometry"]["type"]
    np.testing.assert_array_almost_equal(
        exp["geometry"]["coordinates"], ref["geometry"]["coordinates"]
    )
    assert exp["properties"] == ref["properties"]
    assert exp["assets"].keys() == ref["assets"].keys()
    for k in exp["assets"].keys():
        compare_assets(exp["assets"][k], ref["assets"][k])


def compare_extent(exp: dict[str, Any], ref: dict[str, Any]) -> None:
    assert exp["extent"]["temporal"] == ref["extent"]["temporal"]
    np.testing.assert_array_almost_equal(
        exp["extent"]["spatial"]["bbox"], ref["extent"]["spatial"]["bbox"]
    )
