import datetime as pydatetime
from collections.abc import Sequence
from itertools import chain
from pathlib import Path
from typing import cast
from uuid import UUID, uuid4

import geopandas as gpd
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely import MultiPoint, Point, to_geojson

from stac_generator.generator import StacGenerator
from stac_generator.types import (
    CSVMediaType,
    DateTimeT,
    FrameT,
    PointBandInfo,
    TimeExtentT,
)


# Helper functions
def ensure_name_suffix(name: str, suffix: str) -> str:
    """Ensure that name ends with suffix.
    If name does not end with suffix, add suffix to the end of name

    Args:
        name (str): name
        suffix (str): suffix value

    Returns:
        str: name with suffix
    """
    if name.lower().endswith(suffix):
        return name
    if name.endswith("_"):
        return name + suffix
    return name + "_" + suffix


def create_item_name(collection_name: str, group_name: str | None = None) -> str:
    suffix = group_name + "_item" if group_name else "item"
    # Collection name is guaranteed to contain collection suffix
    assert collection_name.endswith("collection")
    parts = collection_name.rsplit("collection", 1)
    parts[-1] = suffix
    return "".join(parts)


class _PointGenerator(StacGenerator):
    """Create a point stac generator object

    Args:
        data_file (str): path to csv file containing Point information
        X_coord (str): column name representing X coordinate
        Y_coord (str): column name representing Y coordinate
        projection (int, optional): EPSG code. Defaults to 4326 - WGS 84
        date_format (str, optional): date format for parsing time coordinate. Defaults to "ISO8601".
        bands (Sequence[str] | Sequence[PointBandInfo] | None, optional): band information. Defaults to None.
        item_group (Sequence[str] | None, optional): column name that separate points into item groups. Defaults to None.
        catalog_id (str | UUID, optional): id of catalog. Defaults to uuid4().
        catalog_title (str, optional): title of catalog. Defaults to "Auto-generated catalog title".
        catalog_description (str, optional): description of catalog. Defaults to "Auto-generated catalog description".
        collection_id (str | UUID, optional): id of collection. Defaults to uuid4().
        collection_description (str, optional): description of collection. Defaults to "Auto-generated collection description".
        license (str, optional): collection license. Defaults to "MIT".
        keywords (str | None, optional): collection keywords. Defaults to None.
        datetime (DateTimeT | None, optional): Stac Collection collection datetime. Defaults to None.
        start_datetime (DateTimeT | None, optional): Stac Collection start datetime. Defaults to None.
        end_datetime (DateTimeT | None, optional): Stac Collection end datetime. Defaults to None.
    """

    def __init__(
        self,
        # Parameters specific to Point generator
        # read csv params
        data_file: str,
        X_coord: str,
        Y_coord: str,
        projection: int = 4326,  # EPSG code
        T_coord: str | None = None,
        date_format: str = "ISO8601",
        # Item and item partition information
        bands: Sequence[str] | Sequence[PointBandInfo] | None = None,
        item_group: Sequence[str] | None = None,
        # Parameters that should be common to all Generators
        # Catalogue metadata
        catalog_id: str | UUID = uuid4(),  # noqa: B008,
        catalog_title: str = "Auto-generated catalog title",
        catalog_description: str = "Auto-generated catalog description",
        # Collection metadata
        collection_id: str | UUID = uuid4(),  # noqa: B008
        collection_title: str = "Auto-generated collection title",
        collection_description: str = "Auto-generated collection description",
        license: str = "MIT",
        keywords: list[str] | None = None,
        datetime: DateTimeT | None = None,
        start_datetime: DateTimeT | None = None,
        end_datetime: DateTimeT | None = None,
    ) -> None:
        super().__init__(data_type="point", data_file=get_path(data_file), location_file=None)
        self.X_coord = X_coord
        self.Y_coord = Y_coord
        self.T_coord = T_coord
        self.projection = projection

        self.date_format = date_format
        self.bands = bands
        self.item_group = item_group
        self.collection_frame = read_csv(
            self.data_file,
            self.X_coord,
            self.Y_coord,
            self.T_coord,
            self.date_format,
            self.projection,
            self.bands,
            self.item_group,
        )
        # Catalog metadata
        self.catalog_id = ensure_name_suffix(str(catalog_id), "catalog")
        self.catalog_title = catalog_title
        self.catalog_description = catalog_description

        # Collection metadata
        self.collection_name = ensure_name_suffix(str(collection_id), "collection")
        self.collection_title = collection_title
        self.collection_description = collection_description
        self.license = license
        self.keywords = keywords
        self.start_datetime, self.end_datetime = calculate_temporal_extent(
            self.collection_frame, self.T_coord, datetime, start_datetime, end_datetime
        )
        self.datetime = self.end_datetime

        # Shared asset - the csv source file
        self.asset = pystac.Asset(
            href=data_file,
            media_type=CSVMediaType,
            description="Raw point dataset as a csv file",
            roles=["data"],
        )

    # PLACEHOLDER - TODO: CONCRETE Implementation of the methods
    def generate_catalog(self) -> pystac.Catalog:
        return pystac.Catalog(id=self.catalog_id, description=self.catalog_description, title=self.catalog_title)

    # PLACEHOLDER - TODO: CONCRETE Implementation of the methods
    # Note - fail currently due to missing href since item does not have an URL just yet
    def validate_data(self) -> bool:
        return bool(self.collection and self.collection.validate())

    # PLACEHOLDER - TODO: CONCRETE Implementation of the methods
    def validate_stac(self) -> bool:
        return self.validate_data()

    # PLACEHOLDER - Unable to fit the signature
    def generate_item(self, location: str, counter: int) -> pystac.Item:
        return None  # type: ignore

    def generate_items(self) -> list[pystac.Item]:
        # Each Stac Item is fully described by a partition df
        partitions = partition_group_df(self.collection_frame, self.collection_name, self.item_group)
        items: list[pystac.Item] = []
        for item_name, item_df in partitions.items():
            bbox = item_df.total_bounds
            geometry = calculate_geometry(item_df)
            item = pystac.Item(
                id=item_name,
                geometry=to_geojson(geometry),
                bbox=bbox,
                datetime=self.datetime,
                start_datetime=self.start_datetime,
                end_datetime=self.end_datetime,
                assets={"source_file": self.asset},
                properties={"bands": self.bands},
            )
            proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
            proj_ext.apply(epsg=self.projection)
            items.append(item)
        return items

    def generate_collection(self) -> pystac.Collection:
        # Calculate extents
        space_bbox = self.collection_frame.total_bounds
        spatial_extent = pystac.SpatialExtent(space_bbox)
        temporal_extent = pystac.TemporalExtent([[self.start_datetime, self.end_datetime]])

        # Generate collection
        collection = pystac.Collection(
            id=self.collection_name,
            title=self.collection_title,
            description=self.collection_description,
            assets={"source_file": self.asset},
            extent=pystac.Extent(
                spatial=spatial_extent,
                temporal=temporal_extent,
            ),
            license=self.license,
            keywords=self.keywords,
        )
        # Add items to collection
        for item in self.generate_items():
            collection.add_item(item)

        collection.normalize_hrefs("./")
        return collection
