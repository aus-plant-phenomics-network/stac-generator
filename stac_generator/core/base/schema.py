import datetime
import logging
from collections.abc import Sequence
from typing import Annotated, Any, Literal, NotRequired, Required, TypeVar

import pandas as pd
import pytz
from httpx._types import RequestData
from pydantic import BaseModel, BeforeValidator, Field
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
from stac_generator.core.base.utils import get_timezone, is_string_convertible
from stac_generator.exceptions import TimezoneException

T = TypeVar("T", bound="SourceConfig")
ASSET_KEY = "data"
"""Constant describing the primary asset key"""
logger = logging.getLogger(__name__)


class StacCollectionConfig(BaseModel):
    """Contains parameters to pass to Collection constructor. Also contains other metadata except for datetime related metadata.

    This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">Stac Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    # Stac Information
    id: str
    """Item id"""
    title: str | None = "Auto-generated Stac Item"
    """A human readable title describing the item entity. <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#basics>See more</a>"""
    description: str | None = "Auto-generated Stac Item"
    """Detailed multi-line description to fully explain the STAC entity. <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#basics>See more</a>"""
    license: str | None = None
    """License(s) of the data as SPDX License identifier, SPDX License expression, or other - <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#licensing>See more</a>"""
    providers: list[Provider] | None = None
    """A list of providers, which may include all organizations capturing or processing the data or the hosting provider. Providers should be listed in chronological order with the most recent provider being the last element of the list. - <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#provider>See more</a>"""
    platform: str | None = None
    """Unique name of the specific platform to which the instrument is attached. <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#platform>See more</a>"""
    instruments: list[str] | None = None
    """Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1). <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#instrument>See more</a>"""
    constellation: str | None = None
    """Name of the constellation to which the platform belongs. <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#constellation>See more</a>"""
    mission: str | None = None
    """Name of the mission for which data is collected. <a href=https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md#mission>See more</a>"""


class StacItemConfig(StacCollectionConfig):
    """Contains parameters related to collection date, time and timezone.

    A STAC Item's `datetime` field is derived from the combination of `collection_date`, `collection_time` and `timezone`.
    If the asset contains a timeseries, in which some values are not timezone aware, the timestamp is embedded with timezone
    information from the parameter `timezone`.
    """

    collection_date: datetime.date
    """Date when the data is collected"""
    collection_time: datetime.time
    """Time when the data is collected"""
    timezone: str | Literal["utc", "local"] = "local"
    """How timestamps associated with the Item is interpreted. If timezone is local, timezone information is derived from geometry. If timezone is a valid IANA timezone, non tz-aware timestamps will be embedded with timezone information. If an invalid timezone is provided, will raise an error."""

    def get_datetime(self, geometry: Geometry | Sequence[Geometry]) -> pd.Timestamp:
        """Method to derive item's datetime based on collection date, collection time, and potentially geometry"""
        timezone = get_timezone(self.timezone, geometry)
        try:
            local_dt = pd.Timestamp(
                f"{self.collection_date}T{self.collection_time}",
                tzinfo=pytz.timezone(timezone),
            )
        except Exception as e:  # noqa: BLE001
            raise TimezoneException(
                f"Invalid timezone config parameter for asset with id: {self.id}. " + str(e)
            ) from None
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

    location: Annotated[str, BeforeValidator(is_string_convertible)]
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

    def to_common_metadata(self) -> dict[str, Any]:
        """Method to convert config to a python dictionary of common metadata excluding id"""
        return StacCollectionConfig.model_construct(
            **self.model_dump(mode="python", exclude_unset=True, exclude_none=True, exclude={"id"})
        ).model_dump(mode="json", exclude_unset=True, exclude_none=True, warnings=False)

    def to_asset_config(self) -> dict[str, Any]:
        """Abstract method that dictates how config should be serialised that contains the minimum information
        to intepret the asset. SourceConfig subclasses should inherit and override this method.
        """
        raise NotImplementedError

    def to_properties(self) -> dict[str, Any]:
        """Method to convert config to properties dictionary to be added to Item's properties field. This
        includes `timezone` attribute and `stac_generator` key value pairs derived from `to_asset_config`.
        """
        return {
            "timezone": self.timezone,
            "stac_generator": self.to_asset_config(),
            **self.to_common_metadata(),
        }


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
    """Mixin that provides column info field"""

    column_info: list[ColumnInfo] = Field(default_factory=list)
    """List of attributes associated with point/vector data"""
