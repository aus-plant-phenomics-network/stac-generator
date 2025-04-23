from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

import pandas as pd
from httpx._types import PrimitiveData

"""<a href="https://www.rfc-editor.org/rfc/rfc7111">Csv MIME type</a>"""
CsvMediaType = "text/csv"

"""<a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types">Excel MIME type</a>"""
ExcelMediaType = "application/vnd.ms-excel"

"""HTTP Methods"""
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]

"""HTTP URL Query Params"""
QueryParamTypes = (
    Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
    | list[tuple[str, PrimitiveData]]
    | tuple[tuple[str, PrimitiveData], ...]
    | str
    | bytes
)

"""HTTP Header"""
HeaderTypes = (
    Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)

"""HTTP Cookies"""
CookieTypes = dict[str, str] | list[tuple[str, str]]

"""HTTP Body"""
RequestContent = str | bytes | Iterable[bytes]

"""STAC objects"""
StacEntityT = Literal["Item", "ItemCollection", "Collection", "Catalogue"]

"""STAC API HTTP Methods"""
StacAPIMethod = Literal["POST", "PUT"]

Timestamp = pd.Timestamp
TimeSeries = pd.Series
TimeSequence = Sequence[Timestamp] | TimeSeries
