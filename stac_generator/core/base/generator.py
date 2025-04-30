from __future__ import annotations

import abc
import datetime as pydatetime
import json
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Generic, cast

import geopandas as gpd
import numpy as np
import pandas as pd
import pystac
from pyproj import CRS
from pystac.collection import Extent
from pystac.extensions.projection import ItemProjectionExtension
from pystac.utils import datetime_to_str
from shapely import (
    Geometry,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
    box,
    to_geojson,
)
from shapely.geometry import shape

from stac_generator.core.base.schema import (
    SourceConfig,
    StacCollectionConfig,
    T,
)
from stac_generator.core.base.utils import (
    add_timestamps,
    force_write_to_stac_api,
    get_timezone,
    href_is_stac_api_endpoint,
    is_string_convertible,
    localise_timezone,
    parse_href,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from concurrent.futures import Executor

    from stac_generator._types import TimeSequence


logger = logging.getLogger(__name__)


def run_generator(generator: ItemGenerator) -> pystac.Item:
    return generator.generate()


class CollectionGenerator:
    """CollectionGenerator class. User should not need to subclass this class unless greater control over how collection is generated from items is needed."""

    def __init__(
        self,
        collection_config: StacCollectionConfig,
        generators: Sequence[ItemGenerator[T]],
        pool: Executor | None = None,
    ) -> None:
        """CollectionGenerator - generate collection from generators attribute

        :param collection_config: collection metadata
        :type collection_config: StacCollectionConfig
        :param generators: sequence of ItemGenerator subclasses.
        :type generators: Sequence[ItemGenerator]
        """
        self.collection_config = collection_config
        self.generators = generators
        self.pool = pool

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
            if item.datetime is not None:
                min_dt = min(min_dt, item.datetime)
                max_dt = max(max_dt, item.datetime)
            else:
                raise ValueError(
                    f"Unable to determine datetime for item: {item.id}"
                )  # prama: no cover
        min_dt, max_dt = min([min_dt, max_dt]), max([max_dt, min_dt])
        logger.debug(
            f"collection time extent: {[datetime_to_str(min_dt), datetime_to_str(max_dt)]}"
        )
        return pystac.TemporalExtent([[min_dt, max_dt]])

    def _create_collection_from_items(
        self,
        items: Sequence[pystac.Item],
        collection_config: StacCollectionConfig | None = None,
    ) -> pystac.Collection:
        logger.debug("Generating collection from items")
        if collection_config is None:  # pragma: no cover
            raise ValueError("Generating collection requires non null collection config")
        collection = pystac.Collection(
            id=collection_config.id,
            description=(
                collection_config.description
                if collection_config.description
                else f"Auto-generated collection {collection_config.id} with stac_generator"
            ),
            extent=Extent(self.spatial_extent(items), self.temporal_extent(items)),
            title=collection_config.title,
            license=collection_config.license if collection_config.license else "proprietary",
            providers=[
                pystac.Provider.from_dict(item.model_dump()) for item in collection_config.providers
            ]
            if collection_config.providers
            else None,
        )
        collection.add_items(items)
        return collection

    def __call__(self) -> pystac.Collection:
        if self.pool:
            result = list(self.pool.map(run_generator, self.generators))
        else:
            result = [item.generate() for item in self.generators]
        return self._create_collection_from_items(result, self.collection_config)


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
        config: dict[str, Any] | T,
    ) -> None:
        """Base ItemGenerator object. Users should extend this class for handling different file extensions.

        :param configs: source data configs - either from csv config or yaml/json
        :type configs: Mapping[str, Any]
        """
        logger.debug(
            f"validating config: {config.get('id', 'invalid') if isinstance(config, dict) else getattr(config, 'id', 'invalid')}"
        )
        if isinstance(config, self.source_type):
            self.config = config
        elif isinstance(config, dict):
            self.config = self.source_type(**config)
        else:
            raise TypeError(f"Invalid config type: {type(config)}")

    @abc.abstractmethod
    def generate(self) -> pystac.Item:
        """Abstract method that handles `pystac.Item` generation from the appropriate config"""
        raise NotImplementedError


class VectorGenerator(ItemGenerator[T]):
    @classmethod
    def __class_getitem__(cls, source_type: type) -> type:
        kwargs = {"source_type": source_type}
        return type(f"VectorGenerator[{source_type.__name__}]", (VectorGenerator,), kwargs)

    @staticmethod
    def geometry(  # noqa: C901
        df: gpd.GeoDataFrame,
    ) -> Geometry:
        """Calculate the geometry from geopandas dataframe.

        If geopandas dataframe has only one item, the geometry will be that of the item.
        If geopandas dataframe has less than 10 items of the same type, the geometry will be the Multi version of the type.
        Note that MultiPoint will be unpacked into points for the 10 items limit.
        If there are more than 10 items of the same type or there are items of different types i.e. Point and LineString, the returned
        geometry will be the Polygon of the bounding box. Note that Point and MultiPoint are treated as the same type (so are type and its Multi version).

        :param df: input dataframe
        :type df: gpd.GeoDataFrame
        """
        points: Sequence[Geometry] = df["geometry"].unique()
        # One item
        if len(points) == 1:
            return points[0]
        # Multiple Items of the same type
        curr_type = None
        curr_collection: list[Geometry] = []
        for point in points:
            if curr_type is None:
                match point:
                    case Point() | MultiPoint():
                        curr_type = MultiPoint
                    case LineString() | MultiLineString():
                        curr_type = MultiLineString
                    case Polygon() | MultiPolygon():
                        curr_type = MultiPolygon
                    case _:  # pragma: no cover
                        return box(*df.total_bounds)
            if isinstance(point, Point) and curr_type == MultiPoint:
                curr_collection.append(point)
            elif isinstance(point, MultiPoint) and curr_type == MultiPoint:
                curr_collection.extend(point.geoms)
            elif isinstance(point, LineString) and curr_type == MultiLineString:
                curr_collection.append(point)
            elif isinstance(point, MultiLineString) and curr_type == MultiLineString:
                curr_collection.extend(point.geoms)
            elif isinstance(point, Polygon) and curr_type == MultiPolygon:
                curr_collection.append(point)
            elif isinstance(point, MultiPolygon) and curr_type == MultiPolygon:
                curr_collection.extend(point.geoms)
            else:
                return box(*df.total_bounds)
        if len(curr_collection) > 10:
            return box(*df.total_bounds)
        return cast(Geometry, curr_type)(curr_collection)

    @staticmethod
    def df_to_item(
        df: gpd.GeoDataFrame,
        assets: dict[str, pystac.Asset],
        source_config: SourceConfig,
        properties: dict[str, Any],
        epsg: int = 4326,
        time_column: str | None = None,
    ) -> pystac.Item:
        """Convert geopandas dataframe to pystac.Item

        :param df: input dataframe
        :type df: gpd.GeoDataFrame
        :param assets: source data asset_
        :type assets: dict[str, pystac.Asset]
        :param source_config: config
        :type source_config: SourceConfig
        :param properties: pystac Item properties
        :type properties: dict[str, Any]
        :param time_col: time_col if there are time information in the input df, defaults to None
        :type time_col: str | None, optional
        :param epsg: epsg information, defaults to 4326
        :type epsg: int, optional
        :return: generated pystac Item
        :rtype: pystac.Item
        """
        crs = cast(CRS, df.crs)
        # Convert to WGS 84 for computing geometry and bbox
        df.to_crs(epsg=4326, inplace=True)
        geometry = box(*df.total_bounds)
        item_tz = get_timezone(source_config.timezone, geometry)
        item_ts = source_config.get_datetime(geometry)

        geometry = json.loads(to_geojson(VectorGenerator.geometry(df)))

        # Process timestamps
        if time_column is None:
            # Item TS should be UTC by default
            timestamps: TimeSequence = [item_ts]
            start_datetime = item_ts
            end_datetime = item_ts
        else:
            sorted_ts = pd.Series(np.sort(df[time_column].unique()))  # Sorted unique values
            timestamps = localise_timezone(sorted_ts, item_tz)
            start_datetime = timestamps.min()
            end_datetime = timestamps.max()
        add_timestamps(properties, timestamps)

        item = pystac.Item(
            source_config.id,
            bbox=df.total_bounds.tolist(),
            geometry=geometry,
            datetime=item_ts,
            properties=properties,
            assets=assets,
            start_datetime=start_datetime,
            end_datetime=end_datetime,
        )
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.apply(epsg=epsg, wkt2=crs.to_wkt())
        return item


class StacSerialiser:  # pragma: no cover
    def __init__(self, generator: CollectionGenerator, href: str | Path) -> None:
        self.generator = generator
        self.collection = generator()
        self.href = is_string_convertible(href)

    def pre_serialisation_hook(self, collection: pystac.Collection, href: str) -> None:
        """Hook that can be overwritten to provide pre-serialisation functionality.
        By default, this normalises collection href and performs validation

        :param collection: collection object
        :type collection: pystac.Collection
        :param href: serialisation href
        :type href: str
        """
        logger.debug("Validating generated collection and items")
        collection.normalize_hrefs(href)
        collection.validate_all()

    def __call__(self) -> None:
        self.pre_serialisation_hook(self.collection, self.href)
        if href_is_stac_api_endpoint(self.href):
            self.to_api()
        else:
            self.to_json()
        logger.info(f"successfully save collection {self.collection.id} to {self.href}")

    @staticmethod
    def prepare_collection_configs(
        collection_generator: CollectionGenerator,
    ) -> list[dict[str, Any]]:
        items = collection_generator.generators
        result = []
        for item in items:
            result.append(StacSerialiser.prepare_config(item.config))
        return result

    @staticmethod
    def prepare_config(config: T) -> dict[str, Any]:
        return config.model_dump(
            mode="json",
            exclude_none=True,
            exclude_defaults=True,
            exclude_unset=True,
        )

    def save_collection_config(self, dst: str | Path) -> None:
        config = self.prepare_collection_configs(self.generator)
        with Path(dst).open("w") as file:
            json.dump(config, file)

    @staticmethod
    def save_configs(configs: Sequence[T], dst: str | Path) -> None:
        config = [StacSerialiser.prepare_config(con) for con in configs]
        with Path(dst).open("w") as file:
            json.dump(config, file)

    def to_json(self) -> None:
        """Generate STAC Collection and save to disk as json files"""
        logger.debug("Saving collection as local json")
        self.collection.save()

    def to_api(self) -> None:
        """_Generate STAC Collection and push to remote API.
        The API will first attempt to send a POST request which will be replaced with a PUT request if a 409 error is encountered
        """
        logger.debug("Saving collection to STAC API")
        force_write_to_stac_api(
            url=parse_href(self.href, "collections"),
            id=self.collection.id,
            json=self.collection.to_dict(),
        )
        for item in self.collection.get_items(recursive=True):
            force_write_to_stac_api(
                url=parse_href(self.href, f"collections/{self.collection.id}/items"),
                id=item.id,
                json=item.to_dict(),
            )
