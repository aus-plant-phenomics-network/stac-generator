import datetime
import json
import logging
from collections.abc import Sequence
from typing import Any, Literal, NotRequired, Required, TypeVar

import pandas as pd
import pytz
from httpx._types import RequestData
from pydantic import BaseModel, Field, field_validator
from shapely import Geometry
from stac_pydantic.shared import Provider
from typing_extensions import TypedDict

from stac_generator._types import (
    CookieTypes,
    HeaderTypes,
    HTTPMethod,
    QueryParamTypes,
    RequestContent,
)
from stac_generator.core.base.utils import get_timezone
from stac_generator.exceptions import TimezoneException

T = TypeVar("T", bound="SourceConfig")
ASSET_KEY = "data"
logger = logging.getLogger(__name__)


class StacCollectionConfig(BaseModel):
    """Contains parameters to pass to Collection constructor. Also contains other metadata except for datetime related metadata.

    Collection's datetime, start_datetime and end_datetime will be derived from the time information of its children items

    This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">Stac Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    # Stac Information
    id: str
    """Item id"""
    title: str | None = "Auto-generated Stac Item"
    """A human readable title describing the item entity. https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#basics"""
    description: str | None = "Auto-generated Stac Item"
    """Detailed multi-line description to fully explain the STAC entity. https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#basics"""
    license: str | None = None
    """License(s) of the data as SPDX License identifier, SPDX License expression, or other - https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#licensing"""
    providers: list[Provider] | None = None
    """A list of providers, which may include all organizations capturing or processing the data or the hosting provider. Providers should be listed in chronological order with the most recent provider being the last element of the list. - https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#provider"""
    platform: str | None = None
    """Unique name of the specific platform to which the instrument is attached. https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#platform"""
    instruments: list[str] | None = None
    """Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1). https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#instrument"""
    constellation: str | None = None
    """Name of the constellation to which the platform belongs. https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#constellation"""
    mission: str | None = None
    """Name of the mission for which data is collected. https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#mission"""


class StacItemConfig(StacCollectionConfig):
    """Contains parameters to pass to Item constructor. Also contains other metadata except for datetime related metadata.

    Item's datetime will be superseded by `collection_date` and `collection_time` recorded in local timezone. The STAC `datetime`
    metadata is obtained from the method `get_datetime` by providing the local timezone, which will be automatically derived from
    the crs information.

    This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">Stac Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    collection_date: datetime.date
    """Date when the data is collected"""
    collection_time: datetime.time
    """Time when the data is collected"""
    timezone: str | Literal["utc", "local"] = "local"
    """Timezone"""

    def get_datetime(self, geometry: Geometry | Sequence[Geometry]) -> pd.Timestamp:
        timezone = get_timezone(self.timezone, geometry)
        try:
            local_dt = pd.Timestamp(
                f"{self.collection_date}T{self.collection_time}",
                tzinfo=pytz.timezone(timezone),
            )
        except Exception as e:
            raise TimezoneException("Invalid timezone config parameter") from e
        return local_dt.tz_convert(pytz.timezone("UTC"))


class SourceConfig(StacItemConfig):
    """Base source config that should be subclassed for different file extensions.

    Source files contain raw spatial information (i.e. geotiff, shp, csv) from which
    some Stac metadata can be derived. SourceConfig describes:

    - The access mechanisms for the source file: stored on local disk, or hosted somewhere behind an api endpoint. If the source
    file must be accessed through an endpoint, users can provide additional HTTP information that forms the HTTP request to the host server.
    - Processing information that are unique for the source type. Users should inherit `SourceConfig` for file extensions
    currently unsupported.
    - Additional Stac Metadata from `StacConfig`
    """

    location: str
    """Asset's href"""
    extension: str | None = None
    """Explicit file extension specification. If the file is stored behind an api endpoint, the field `extension` must be provided"""
    # HTTP Parameters
    method: HTTPMethod | None = "GET"
    """HTTPMethod to acquire the file from `location`"""
    params: QueryParamTypes | None = None
    """HTTP query params for getting file from `location`"""
    headers: HeaderTypes | None = None
    """HTTP query headers for getting file from `location`"""
    cookies: CookieTypes | None = None
    """HTTP query cookies for getting file from `location`"""
    content: RequestContent | None = None
    """HTTP query body content for getting file from `location`"""
    data: RequestData | None = None
    """HTTP query body content for getting file from `location`"""
    json_body: Any = None
    """HTTP query body content for getting file from `location`"""

    def to_properties(self) -> dict[str, Any]:
        return self.model_dump(mode="json", exclude_unset=True, exclude_none=True)


DTYPE = Literal[
    "str",
    "int",
    "bool",
    "float",
    "int8",
    "int16",
    "int32",
    "int64",
    "uint8",
    "uint16",
    "uint32",
    "uint64",
    "float16",
    "float32",
    "float64",
    "cint16",
    "cint32",
    "cfloat32",
    "cfloat64",
    "other",
]


class ColumnInfo(TypedDict):
    """TypedDict description of GeoDataFrame columns. Used for describing vector/point attributes"""

    name: Required[str]
    """Column name"""
    description: NotRequired[str]
    """Column description"""
    dtype: NotRequired[DTYPE]
    """Column data type"""


class HasColumnInfo(BaseModel):
    column_info: list[ColumnInfo] = Field(default_factory=list)
    """List of attributes associated with point/vector data"""

    @field_validator("column_info", mode="before")
    @classmethod
    def coerce_to_object(cls, v: str | list[ColumnInfo] | None) -> list[ColumnInfo]:
        """Convert json serialised string of column info into matched object"""
        if v is None:
            return []
        if isinstance(v, list):
            return v
        parsed = json.loads(v)
        if not isinstance(parsed, list):
            raise ValueError(
                "column_info field expects a json serialisation of a list of ColumnInfo or a list of string"
            )
        return parsed
