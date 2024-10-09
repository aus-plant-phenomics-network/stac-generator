import datetime
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

import geopandas as gpd
import pandas as pd
from httpx._types import PrimitiveData

# Generic Types
"""Number"""
NumberT = int | float
"""Datetime"""
DateTimeT = datetime.datetime
"""tuple of start and end dates"""
TimeExtentT = tuple[DateTimeT | None, DateTimeT | None]  # (start_datetime, end_datetime) format

"""<a href="https://www.rfc-editor.org/rfc/rfc7111">CSV MIME type</a>"""
CSVMediaType = "text/csv"
"""<a href="https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types">Excel MIME type</a>"""
ExcelMediaType = "application/vnd.ms-excel"

"""Pandas DataFrame"""
PDFrameT = pd.DataFrame

"""Geopandas DataFrame"""
FrameT = gpd.GeoDataFrame

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
