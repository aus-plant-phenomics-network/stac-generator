from __future__ import annotations

import datetime
from typing import Any, Generic, Self, TypeVar, cast

from httpx._types import (
    RequestData,  # noqa: TCH002
)
from pandera import DataFrameModel
from pandera.api.pandas.model_config import BaseConfig
from pandera.engines.pandas_engine import PydanticModel
from pydantic import BaseModel, model_validator
from stac_pydantic.shared import StacCommonMetadata

from stac_generator.types import (  # noqa: TCH001
    CookieTypes,
    HeaderTypes,
    HTTPMethod,
    QueryParamTypes,
    RequestContent,
    STACEntityT,
)

T = TypeVar("T", bound="SourceConfig")


class STACConfig(StacCommonMetadata):
    """This config provides additional information that can not be derived from source file, which includes
    <a href="https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md">STAC Common Metadata</a>
    and other descriptive information such as the id of the new entity
    """

    # STAC Information
    id: str
    """Item/collection id"""
    prefix: str | None = None
    """Item prefix when generating multiple items. If prefix is not provided, will use id as prefix for generating contained STAC entities"""

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


class SourceConfig(STACConfig):
    """Base source config that should be subclassed for different file extensions.

    Source files contain raw spatial information (i.e. geotiff, shp, csv) from which
    some STAC metadata can be derived. SourceConfig describes:

    - The access mechanisms for the source file: stored on local disk, or hosted somewhere behind an api endpoint. If the source
    file must be accessed through an endpoint, users can provide additional HTTP information that forms the HTTP request to the host server.
    - Processing information that are unique for the source type. Users should inherit `SourceConfig` for file extensions
    currently unsupported.
    - Additional STAC Metadata from `STACConfig`
    """

    location: str
    """Asset's href. If `local` is not provided, will be used as endpoint for fetching data file, using other config parameters.
    If the file is on disk, it is acceptable to set location as ./path/to/source/file
    """
    local: str | None = None
    """Path to the source file on local disk. This is for reading in and processing local file.
    If local is not provided, HTTP methods and other parameters must be provided for reading in the file from `location` field"""
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
        return (cast(str, self.local)).split(".")[-1]

    @model_validator(mode="after")
    def validate_require_extension_when_source_is_remote(self) -> Self:
        if self.local is None and self.extension is None:
            raise ValueError(
                "If source is must be accessed through an endpoint, extension field must be specified"
            )
        return self


class LoadConfig(BaseModel):
    entity: STACEntityT
    """STAC Entity type - Item, ItemCollection, Collection, Catalog"""
    json_location: str | None = None
    """STAC Json file on disk"""
    stac_api_endpoint: str | None = None
    """STAC API Endpoint"""

    @model_validator(mode="after")
    def validate_field(self) -> Self:
        if self.json_location is None and self.stac_api_endpoint is None:
            raise ValueError("One of json_location or stac_api_endpoint field must be not None")
        return self


class DataFrameSchema(Generic[T]):
    @classmethod
    def __class_getitem__(cls, cfg_type: type):
        class Config(BaseConfig):
            dtype = PydanticModel(cfg_type)
            coerce = True
            add_missing_columns = True

        return type(
            "DataFrameSchema",
            (DataFrameModel,),
            {"Config": Config},
        )
