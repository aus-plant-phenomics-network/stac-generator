from __future__ import annotations

import abc
import datetime as pydatetime
import json
import logging
from typing import TYPE_CHECKING, Any, Generic

import geopandas as gpd
import numpy as np
import pystac
from pystac.collection import Extent
from pystac.extensions.projection import ItemProjectionExtension
from pystac.utils import datetime_to_str, str_to_datetime
from shapely import GeometryCollection, to_geojson
from shapely.geometry import shape

from stac_generator.base.schema import (
    SourceConfig,
    StacCollectionConfig,
    T,
)
from stac_generator.base.utils import (
    force_write_to_stac_api,
    href_is_stac_api_endpoint,
    parse_href,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    from shapely import Geometry

    from stac_generator._types import TimeExtentT

logger = logging.getLogger(__name__)


class CollectionGenerator:
    """CollectionGenerator class. User should not need to subclass this class unless greater control over how collection is generated from items is needed."""

    def __init__(
        self,
        collection_cfg: StacCollectionConfig,
        generators: Sequence[ItemGenerator],
    ) -> None:
        """CollectionGenerator - generate collection from generators attribute

        :param collection_cfg: collection metadata
        :type collection_cfg: StacCollectionConfig
        :param generators: sequence of ItemGenerator subclasses.
        :type generators: Sequence[ItemGenerator]
        """
        self.collection_cfg = collection_cfg
        self.generators = generators

    @staticmethod
    def spatial_extent(items: Sequence[pystac.Item]) -> pystac.SpatialExtent:
        """Extract a collection's spatial extent based on geometry information of its items

        :param items: a list of children items in the collection
        :type items: Sequence[pystac.Item]
        :return: a bbox enveloping all items
        :rtype: pystac.SpatialExtent
        """
        geometries: list[Geometry] = []
        for item in items:
            if (geo := item.geometry) is not None:
                geometries.append(shape(geo))
        geo_series = gpd.GeoSeries(data=geometries)
        bbox = geo_series.total_bounds.tolist()
        logger.debug(f"collection bbox: {bbox}")
        return pystac.SpatialExtent(bbox)

    @staticmethod
    def temporal_extent(items: Sequence[pystac.Item]) -> pystac.TemporalExtent:
        """Extract a collection's temporal extent based on time information of its items

        :param items: a list of children items in the collection
        :type items: Sequence[pystac.Item]
        :return: [start_time, end_time] enveloping all items
        :rtype: pystac.TemporalExtent
        """
        min_dt = pydatetime.datetime.now(pydatetime.UTC)
        max_dt = pydatetime.datetime(1, 1, 1, tzinfo=pydatetime.UTC)
        for item in items:
            if "start_datetime" in item.properties and "end_datetime" in item.properties:
                min_dt = min(min_dt, str_to_datetime(item.properties["start_datetime"]))
                max_dt = max(max_dt, str_to_datetime(item.properties["end_datetime"]))
            elif item.datetime is not None:
                min_dt = min(min_dt, item.datetime)
                max_dt = max(max_dt, item.datetime)
        max_dt = max(max_dt, min_dt)
        logger.debug(
            f"collection time extent: {[datetime_to_str(min_dt), datetime_to_str(max_dt)]}"
        )
        return pystac.TemporalExtent([[min_dt, max_dt]])

    def _create_collection_from_items(
        self,
        items: list[pystac.Item],
        collection_cfg: StacCollectionConfig | None = None,
    ) -> pystac.Collection:
        logger.debug("generating collection from items")
        if collection_cfg is None:
            raise ValueError("Generating collection requires non null collection config")
        collection = pystac.Collection(
            id=collection_cfg.id,
            description=(
                collection_cfg.description
                if collection_cfg.description
                else f"Auto-generated collection {collection_cfg.id} with stac_generator"
            ),
            extent=Extent(self.spatial_extent(items), self.temporal_extent(items)),
            title=collection_cfg.title,
            license=collection_cfg.license if collection_cfg.license else "proprietary",
            providers=[
                pystac.Provider.from_dict(item.model_dump()) for item in collection_cfg.providers
            ]
            if collection_cfg.providers
            else None,
        )
        collection.add_items(items)
        return collection

    def create_collection(self) -> pystac.Collection:
        """Generate collection from all gathered items

        Spatial extent is the bounding box enclosing all items
        Temporal extent is the time interval enclosing temporal extent of all items. Note that this value is automatically calculated
        and provided temporal extent fields (start_datetime, end_datetime) at collection level will be ignored

        :return: generated collection
        :rtype: pystac.Collection
        """
        items = []
        for generator in self.generators:
            items.extend(generator.create_items())
        return self._create_collection_from_items(items, self.collection_cfg)


class ItemGenerator(abc.ABC, Generic[T]):
    """Base ItemGenerator object. Users should extend this class for handling different file extensions."""

    source_type: type[T]
    """SourceConfig subclass that contains information used for parsing the source file"""

    @classmethod
    def __class_getitem__(cls, source_type: type) -> type:
        kwargs = {"source_type": source_type}
        return type(f"ItemGenerator[{source_type.__name__}]", (ItemGenerator,), kwargs)

    def __init__(
        self,
        configs: list[dict[str, Any]],
    ) -> None:
        """Base ItemGenerator object. Users should extend this class for handling different file extensions.

        :param configs: source data configs - either from csv config or yaml/json
        :type configs: list[dict[str, Any]]
        """
        logger.debug("validating config")
        self.configs = [self.source_type(**config) for config in configs]

    @abc.abstractmethod
    def create_item_from_config(self, source_cfg: T) -> pystac.Item:
        """Abstract method that handles `pystac.Item` generation from the appropriate config"""
        raise NotImplementedError

    def create_items(self) -> list[pystac.Item]:
        """Generate STAC Items from `configs` metadata

        :return: list of generated STAC Item
        :rtype: list[pystac.Item]
        """
        logger.debug(f"generating items using {self.__class__.__name__}")
        items = []
        for config in self.configs:
            items.append(self.create_item_from_config(config))
        return items


class VectorGenerator(ItemGenerator[T]):
    @classmethod
    def __class_getitem__(cls, source_type: type) -> type:
        kwargs = {"source_type": source_type}
        return type(f"VectorGenerator[{source_type.__name__}]", (VectorGenerator,), kwargs)

    @staticmethod
    def geometry(
        df: gpd.GeoDataFrame,
    ) -> Geometry:
        """Calculate the geometry from geopandas dataframe.

        If geopandas dataframe has only one item, the geometry will be that of the item.
        If geopandas dataframe has multiple items, the geometry will be a GeometryCollection with
        all geometries

        :param df: input dataframe
        :type df: gpd.GeoDataFrame
        """
        points: Sequence[Geometry] = df["geometry"].unique()
        if len(points) == 1:
            return points[0]
        return GeometryCollection(points)

    @staticmethod
    def temporal_extent(
        df: gpd.GeoDataFrame | None = None,
        time_col: str | None = None,
        datetime: pydatetime.datetime | None = None,
        start_datetime: pydatetime.datetime | None = None,
        end_datetime: pydatetime.datetime | None = None,
    ) -> TimeExtentT:
        """Generate [start_datetime, end_datetime] property fields for a STAC Item

        If both df and time_col are provided, the temporal extent will be calculated as the min and max of time_col values in
        df, provided the values are of datetime type.

        If start_datetime and end_datetime are provided, return as is.

        If datetime is provided, return [datetime, datetime]

        :param df: dataframe with a time column. defaults to None
        :type df: gpd.GeoDataFrame | None, optional
        :param time_col: time column in df, defaults to None
        :type time_col: str | None, optional
        :param datetime: datetime value, defaults to None
        :type datetime: pydatetime.datetime | None, optional
        :param start_datetime: start_datetime value, defaults to None
        :type start_datetime: pydatetime.datetime | None, optional
        :param end_datetime: end_datetime value, defaults to None
        :type end_datetime: pydatetime.datetime | None, optional
        :raises KeyError: if both df and time_col are provided as argument, but time_col is not a valid column in df
        :raises ValueError: time_col does not have datetime type
        :raises ValueError: all parameters are None.
        :return: [start_datetime, end_datetime] information
        :rtype: TimeExtentT
        """
        if df is not None and isinstance(time_col, str):
            if time_col not in df.columns:
                raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
            if not np.issubdtype(df[time_col].dtype, np.datetime64):
                raise ValueError(
                    f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}"
                )
            min_T, max_T = df[time_col].min(), df[time_col].max()
            return (min_T, max_T)
        if start_datetime and end_datetime:
            return start_datetime, end_datetime
        if datetime:
            return datetime, datetime
        raise ValueError(
            "If datetime is None, both start_datetime and end_datetime values must be provided"
        )

    @staticmethod
    def df_to_item(
        df: gpd.GeoDataFrame,
        assets: dict[str, pystac.Asset],
        source_cfg: SourceConfig,
        properties: dict[str, Any],
        time_col: str | None = None,
        epsg: int = 4326,
    ) -> pystac.Item:
        """Convert geopandas dataframe to pystac.Item

        :param df: input dataframe
        :type df: gpd.GeoDataFrame
        :param assets: source data asset_
        :type assets: dict[str, pystac.Asset]
        :param source_cfg: config
        :type source_cfg: SourceConfig
        :param properties: pystac Item properties
        :type properties: dict[str, Any]
        :param time_col: time_col if there are time information in the input df, defaults to None
        :type time_col: str | None, optional
        :param epsg: epsg information, defaults to 4326
        :type epsg: int, optional
        :return: generated pystac Item
        :rtype: pystac.Item
        """
        start_datetime, end_datetime = VectorGenerator.temporal_extent(
            df,
            time_col,
            source_cfg.datetime,
            source_cfg.start_datetime,
            source_cfg.end_datetime,
        )
        geometry = json.loads(to_geojson(VectorGenerator.geometry(df)))
        item = pystac.Item(
            source_cfg.id,
            bbox=df.total_bounds.tolist(),
            geometry=geometry,
            datetime=end_datetime,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
            properties=properties,
            assets=assets,
        )
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.apply(epsg=epsg)
        return item


class StacSerialiser:
    def __init__(self, generator: CollectionGenerator, href: str) -> None:
        self.generator = generator
        self.collection = generator.create_collection()
        self.href = href
        StacSerialiser.pre_serialisation_hook(self.collection, self.href)

    @staticmethod
    def pre_serialisation_hook(collection: pystac.Collection, href: str) -> None:
        """Hook that can be overwritten to provide pre-serialisation functionality.
        By default, this normalises collection href and performs validation

        :param collection: collection object
        :type collection: pystac.Collection
        :param href: serialisation href
        :type href: str
        """
        logger.debug("validating generated collection and items")
        collection.normalize_hrefs(href)
        breakpoint()
        collection.validate_all()

    def __call__(self) -> None:
        if href_is_stac_api_endpoint(self.href):
            return self.to_json()
        return self.to_api()

    def to_json(self) -> None:
        """Generate STAC Collection and save to disk as json files"""
        logger.debug("saving collection as local json")
        self.collection.save()
        logger.info(f"successfully save collection to {self.href}")

    def to_api(self) -> None:
        """_Generate STAC Collection and push to remote API.
        The API will first attempt to send a POST request which will be replaced with a PUT request if a 409 error is encountered
        """
        logger.debug("save collection to STAC API")
        force_write_to_stac_api(
            url=parse_href(self.href, f"collections/{self.collection.id}"),
            json=self.collection.to_dict(),
        )
        for item in self.collection.get_all_items():
            force_write_to_stac_api(
                url=parse_href(self.href, f"collections/{self.collection.id}/items/{item.id}"),
                json=item.to_dict(),
            )
        logger.info(f"successfully save collection to {self.href}")
