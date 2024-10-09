import datetime
from collections.abc import Iterable, Mapping, Sequence
from typing import Literal

import geopandas as gpd
import pandas as pd
from httpx._types import PrimitiveData

# Generic Types

NumberT = int | float
DateTimeT = datetime.datetime
TimeExtentT = tuple[DateTimeT | None, DateTimeT | None]  # (start_datetime, end_datetime) format
CSVMediaType = "text/csv"  # https://www.rfc-editor.org/rfc/rfc7111
ExcelMediaType = "application/vnd.ms-excel"  # https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/MIME_types/Common_types
PDFrameT = pd.DataFrame
FrameT = gpd.GeoDataFrame
HTTPMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
Mode = Literal["append", "overwrite"]

QueryParamTypes = (
    Mapping[str, PrimitiveData | Sequence[PrimitiveData]]
    | list[tuple[str, PrimitiveData]]
    | tuple[tuple[str, PrimitiveData], ...]
    | str
    | bytes
)

HeaderTypes = (
    Mapping[str, str]
    | Mapping[bytes, bytes]
    | Sequence[tuple[str, str]]
    | Sequence[tuple[bytes, bytes]]
)
CookieTypes = dict[str, str] | list[tuple[str, str]]
RequestContent = str | bytes | Iterable[bytes]

StacEntityT = Literal["Item", "ItemCollection", "Collection", "Catalogue"]
