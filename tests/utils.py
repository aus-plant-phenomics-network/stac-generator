from typing import Any

EXCEPT_KEYS = None


def compare_dict_except(
    first: dict[Any, Any],
    second: dict[Any, Any],
    keys: set[str] | None = EXCEPT_KEYS,
) -> None:
    if not keys:
        assert first == second
    else:
        first_keys = set(first.keys()) - keys
        second_keys = set(second.keys()) - keys
        assert first_keys == second_keys
        for k in first_keys:
            assert first[k] == second[k]
