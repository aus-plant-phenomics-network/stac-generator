import datetime
from typing import Any, TypeVar

import pytz
from httpx._types import (
    RequestData,
)
from pydantic import BaseModel
from stac_pydantic.shared import Provider, UtcDatetime

from stac_generator._types import (
    CookieTypes,
    HeaderTypes,
    HTTPMethod,
    QueryParamTypes,
    RequestContent,
)

T = TypeVar("T", bound="SourceConfig")


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
    title: str = "Auto-generated Stac Item"
    """A human readable title describing the item entity."""
    description: str = "Auto-generated Stac Item"
    """Detailed multi-line description to fully explain the STAC entity. """
    license: str | None = None
    """License(s) of the data as SPDX License identifier, SPDX License expression, or other"""
    providers: list[Provider] | None = None
    """A list of providers, which may include all organizations capturing or processing the data or the hosting provider. Providers should be listed in chronological order with the most recent provider being the last element of the list."""
    platform: str | None = None
    """Unique name of the specific platform to which the instrument is attached."""
    instruments: list[str] | None = None
    """Name of instrument or sensor used (e.g., MODIS, ASTER, OLI, Canon F-1)."""
    constellation: str | None = None
    """Name of the constellation to which the platform belongs."""
    mission: str | None = None
    """Name of the mission for which data is collected."""


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
    """Date in local timezone of when the data is collected"""
    collection_time: datetime.time
    """Time in local timezone of when the data is collected"""

    def get_datetime(self, timezone: str) -> UtcDatetime:
        local_dt = datetime.datetime.combine(
            self.collection_date, self.collection_time, tzinfo=pytz.timezone(timezone)
        )
        return local_dt.astimezone(datetime.UTC)


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

    @property
    def source_extension(self) -> str:
        if self.extension:
            return self.extension
        return self.location.split(".")[-1]
