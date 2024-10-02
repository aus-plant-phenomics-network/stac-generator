import datetime as pydatetime
from collections.abc import Sequence
from itertools import chain
from pathlib import Path
from typing import Any, Literal, cast
from uuid import UUID, uuid4

import numpy as np
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension

from stac_generator.generator import StacGenerator
from stac_generator.typing import (
    BBoxT,
    CSVMediaType,
    DateTimeT,
    FrameT,
    GeometryObj,
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


def get_path(path: str | Path) -> Path:
    if isinstance(path, Path):
        return path
    return Path(path)


def calculate_spatial_extent(
    df: FrameT,
    X_coord: str,
    Y_coord: str,
) -> BBoxT:
    """Get bounding box from all points in a dataframe based on GeoJSON specification.
    Assume X_coord and Y_coord values are WGS 84 lat lon coordinates.

    Args:
        df (FrameT): input dataframe containing X_coord and Y_coord columns
        X_coord (str): name of X column
        Y_coord (str): name of Y column

    Returns:
        BBoxT: Bounding box coordinate
    """
    min_X, max_X = float(df[X_coord].min()), float(df[X_coord].max())
    min_Y, max_Y = float(df[Y_coord].min()), float(df[Y_coord].max())
    return [min_X, min_Y, max_X, max_Y]


def calculate_temporal_extent(
    df: FrameT | None = None,
    time_col: str | None = None,
    datetime: DateTimeT | None = None,
    start_datetime: DateTimeT | None = None,
    end_datetime: DateTimeT | None = None,
) -> TimeExtentT:
    """Get temporal extent based on STAC specification. Use start_datetime and end_datetime if provided.
    Otherwise use datetime if provided. If the dataframe and time col is provided, will obtain the
    start datetime, end date time from the dataframe. Otherwise get current UTC time.

    Args:
        df (FrameT | None, optional): provided dataframe. Defaults to None.
        time_col (str | None, optional): name of time column. Defaults to None.
        datetime (DateTimeT | None, optional): datetime. Defaults to None.
        start_datetime (DateTimeT | None, optional): start_datetime. Defaults to None.
        end_datetime (DateTimeT | None, optional): end_datetime. Defaults to None.

    Returns:
        TimeExtentT: start datetime, end_datetime
    """
    if start_datetime and end_datetime:
        return start_datetime, end_datetime
    if datetime:
        return None, datetime
    if df is not None and isinstance(time_col, str):
        if time_col not in df.columns:
            raise KeyError(f"Cannot find time_col: {time_col} in given dataframe")
        if not isinstance(df[time_col].dtype, DateTimeT):
            raise ValueError(f"Dtype of time_col: {time_col} must be of datetime type: {df[time_col].dtype}")
        min_T, max_T = df[time_col].min(), df[time_col].max()
        return (min_T, max_T)
    return None, pydatetime.datetime.now(pydatetime.UTC)


def calculate_geometry(
    df: FrameT,
    X_coord: str = "X",
    Y_coord: str = "Y",
) -> GeometryObj:
    coords = np.unique(df.loc[:, [X_coord, Y_coord]].values, axis=0)
    coord_type: Literal["Point", "MultiPoint"] = "Point" if len(coords) == 1 else "MultiPoint"
    return GeometryObj(type=coord_type, coordinates=coords)


def read_csv(
    src_path: str,
    X_coord: str,
    Y_coord: str,
    T_coord: str | None = None,
    date_format: str = "ISO8601",
    bands: Sequence[str] | Sequence[PointBandInfo] | None = None,
    item_group: Sequence[str] | None = None,
) -> FrameT:
    parse_dates = [T_coord] if isinstance(T_coord, str) else False
    usecols = None
    # If band info is provided, only read in the required columns + the X and Y coordinates
    if bands:
        if isinstance(bands[0], str):
            usecols = list(bands)
        else:
            usecols = [item["name"] for item in cast(Sequence[PointBandInfo], bands)]
        usecols.extend([X_coord, Y_coord])
        if T_coord:
            usecols.append(T_coord)
        # If item group provided -> read in
        if item_group:
            usecols.extend(item_group)
    return pd.read_csv(src_path, parse_dates=parse_dates, date_format=date_format, usecols=usecols)  # type: ignore[call-overload]


def partition_group_df(
    df: FrameT,
    collection_name: str,
    item_group: Sequence[str] | None = None,
) -> dict[str, FrameT]:
    """Partition dataframe into sub-dataframe based on fields in item_group.
    Each partition will be assigned an item name obtained from collection name and field values.

    E.g. If collection name is `point_data` and `item_group = ["sites"]` with values being `["A", "B"]`.
    The resulting item names will be `point_data_site_A_item` and `point_data_site_B_item`.

    If `item_group` is not provided, return a single collection item which is the full dataframe

    Args:
        df (FrameT): source dataframe
        collection_name (str): name of the collection
        item_group (Sequence[str] | None, optional): fields to partition the df. Must be present in the original df. Defaults to None.

    Returns:
        dict[str, FrameT]: mapping of group name to sub_df
    """
    if not item_group:
        item_name = create_item_name(collection_name)
        return {item_name: df}
    partition_df = df.groupby(item_group).apply(lambda group: group.drop_duplicates())  # type: ignore[call-overload]
    partition_df = partition_df.reset_index(level=-1, drop=True)
    df_group = {}
    for i in range(len(partition_df)):
        idx = (
            partition_df.index[i] if len(item_group) != 1 else [partition_df.index[i]]
        )  # If item_group has one single item, convert idx to list of 1
        group_name = "_".join([str(item) for item in chain(*zip(item_group, idx, strict=True))])
        item_name = create_item_name(collection_name, group_name)
        df_group[item_name] = partition_df.loc[idx, :].reset_index(drop=True)
    return df_group


class PointGenerator(StacGenerator):
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
        datetime (DateTimeT | None, optional): STAC Collection collection datetime. Defaults to None.
        start_datetime (DateTimeT | None, optional): STAC Collection start datetime. Defaults to None.
        end_datetime (DateTimeT | None, optional): STAC Collection end datetime. Defaults to None.
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
        **kwargs: Any,
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
        # Each STAC Item is fully described by a partition df
        partitions = partition_group_df(self.collection_frame, self.collection_name, self.item_group)
        items: list[pystac.Item] = []
        for item_name, item_df in partitions.items():
            bbox = calculate_spatial_extent(item_df, self.X_coord, self.Y_coord)
            geometry = calculate_geometry(item_df, self.X_coord, self.Y_coord)
            item = pystac.Item(
                id=item_name,
                geometry=cast(dict[str, Any], geometry),
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
        space_bbox = calculate_spatial_extent(df=self.collection_frame, X_coord=self.X_coord, Y_coord=self.Y_coord)
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
        return collection
