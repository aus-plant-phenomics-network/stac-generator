from __future__ import annotations

import datetime
from typing import Any, TypeVar

from httpx._types import (
    RequestData,  # noqa: TCH002
)
from pydantic import model_validator
from stac_pydantic.shared import StacCommonMetadata as _StacCommonMetaData

from stac_generator._types import (  # noqa: TCH001
    CookieTypes,
    HeaderTypes,
    HTTPMethod,
    QueryParamTypes,
    RequestContent,
)

T = TypeVar("T", bound="SourceConfig")


class StacCommonMetadata(_StacCommonMetaData):
    """Stac Common Metadata. Automatically sets datetime values to
    current datetime if neither datetime nor start_datetime and end_datetime are provided
    """

    @model_validator(mode="before")
    @classmethod
    def set_datetime(self, data: Any) -> Any:
        if isinstance(data, dict) and (
            ("datetime" not in data or data["datetime"] is None)
            and ("start_datetime" not in data or data["start_datetime"] is None)
            and ("end_datetime" not in data or data["end_datetime"] is None)
        ):
            now = datetime.datetime.now(datetime.UTC)
            data["datetime"] = now
            data["start_datetime"] = now
            data["end_datetime"] = now
        return data


class StacCollectionConfig(StacCommonMetadata):
    """Contains parameters to pass to Collection constructor. Also contains other metadata

    This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">Stac Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    # Stac Information
    id: str
    """Collection id"""
    title: str
    """Collection title"""
    description: str = "Auto-generated Stac Collection"
    """Collection description"""


class StacItemConfig(StacCommonMetadata):
    """Contains parameters to pass to Item constructor.

    This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">Stac Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    id: str
    """Item id - doubles as prefix if there are multiple items extracted from the source file"""
    description: str = "Auto-generated Stac Item"
    """Item description"""


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
    """Asset's href.
    """
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
