import datetime
from typing import Any, cast

import geopandas as gpd
import pystac
from shapely import (
    Geometry,
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from stac_generator.base.schema import StacCollectionConfig

__all__ = (
    "extract_spatial_extent",
    "extract_temporal_extent",
    "geometry_from_dict",
)


def geometry_from_dict(item: dict[str, Any]) -> Geometry:
    if not item:
        raise ValueError("Expects non null geometry")
    if "type" not in item:
        raise ValueError("Invalid geojson geometry object: no type field")
    if item["type"] != "GeometryCollection" and "coordinates" not in item:
        raise ValueError(
            "Invalid geojson geometry object: no coordinates field for non GeometryCollection"
        )
    geometry_type = item["type"]
    coordinates = item.get("coordinates")
    match geometry_type:
        case "Point":
            return Point(cast(list, coordinates))
        case "MultiPoint":
            return MultiPoint(cast(list, coordinates))
        case "LineString":
            return LineString(*cast(list, coordinates))
        case "MultiLineString":
            return MultiLineString(cast(list, coordinates))
        case "Polygon":
            return Polygon(cast(list, coordinates))
        case "MultiPolygon":
            return MultiPolygon(cast(list, coordinates))
        case "GeometryCollection":
            if "geometries" not in item:
                raise ValueError(
                    "Invalid geojson geometry object: no geometries field for GeometryCollection type"
                )
            return GeometryCollection(cast(list, item["geometries"]))
        case _:
            raise ValueError(f"Invalid geojson geometry type: {geometry_type}")


def extract_spatial_extent(items: list[pystac.Item]) -> pystac.SpatialExtent:
    geometries: list[Geometry] = []
    for item in items:
        if (geo := item.geometry) is not None:
            geometries.append(geometry_from_dict(geo))
    geo_series = gpd.GeoSeries(data=geometries)
    bbox = geo_series.total_bounds.tolist()
    return pystac.SpatialExtent(bbox)


def extract_temporal_extent(
    items: list[pystac.Item], collection: StacCollectionConfig | None = None
) -> pystac.TemporalExtent:
    if collection:
        if collection.start_datetime and collection.end_datetime:
            return pystac.TemporalExtent([[collection.start_datetime, collection.end_datetime]])
        return pystac.TemporalExtent([collection.datetime, collection.datetime])
    min_dt = datetime.datetime.now(datetime.UTC)
    max_dt = datetime.datetime(1, 1, 1)  # noqa: DTZ001
    for item in items:
        if "start_datetime" in item.properties and "end_datetime" in item.properties:
            min_dt = min(min_dt, item.properties["start_datetime"])
            max_dt = max(max_dt, item.properties["end_datetime"])
        else:
            if item.datetime is None:
                raise ValueError(
                    "Invalid pystac item. Either datetime or start_datetime and end_datetime values must be provided"
                )
            min_dt = min(min_dt, item.datetime)
            max_dt = max(max_dt, item.datetime)
    max_dt = max(max_dt, min_dt)
    return pystac.TemporalExtent([[min_dt, max_dt]])
