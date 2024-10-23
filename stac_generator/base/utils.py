import datetime
import json
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, Any, cast

import geopandas as gpd
import httpx
import pandas as pd
import pystac
import yaml
from shapely.geometry import shape

from stac_generator.base.schema import StacCollectionConfig

if TYPE_CHECKING:
    from shapely import Geometry


def extract_spatial_extent(items: Sequence[pystac.Item]) -> pystac.SpatialExtent:
    """Extract spatial extent for a collection from child items

    :param items: Sequence of all `pystac.Item`
    :type items: Sequence[pystac.Item]
    :return: spatial extent object
    :rtype: pystac.SpatialExtent
    """
    geometries: list[Geometry] = []
    for item in items:
        if (geo := item.geometry) is not None:
            geometries.append(shape(geo))
    geo_series = gpd.GeoSeries(data=geometries)
    bbox = geo_series.total_bounds.tolist()
    return pystac.SpatialExtent(bbox)


def extract_temporal_extent(
    items: Sequence[pystac.Item], collection: StacCollectionConfig | None = None
) -> pystac.TemporalExtent:
    """Extract spatial extent for a collection from a Sequence of items and collection config.

    If temporal extent (`start_datetime`, `end_datetime` or `datetime`) is in `collection`, generate
    `pystac.TemporalExtent` from those fields. Otherwise, extract the fields from the provided items.

    :param items: Sequence of Items
    :type items: Sequence[pystac.Item]
    :param collection: collection config, defaults to None
    :type collection: StacCollectionConfig | None, optional
    :raises ValueError: if a pystac.Item has neither `datetime` nor both `start_datetime` and `end_datetime`
    :return: extracted temporal extent
    :rtype: pystac.TemporalExtent
    """
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


def href_is_local(href: str) -> bool:
    """Check if href points to a local resource

    :param href: path to resource
    :type href: str
    :return: local or non-local
    :rtype: bool
    """
    return not href.startswith(("http", "https"))


def force_write_to_stac_api(url: str, json: dict[str, Any]) -> None:
    """Force write a json object to a stac api endpoint.
    This function will try sending a POST request and if a 409 error is encountered,
    try sending a PUT request

    :param url: path to stac resource for creation/update
    :type url: str
    :param json: json object
    :type json: dict[str, Any]
    """
    try:
        response = httpx.post(url=url, json=json)
        response.raise_for_status()
    except httpx.HTTPStatusError:
        response = httpx.put(url=url, json=json)
        response.raise_for_status()


def read_source_config(href: str) -> list[dict[str, Any]]:
    if not href.endswith(("json", "yaml", "yml", "csv")):
        raise ValueError(
            "Unsupported extension. We currently allow json/yaml/csv files to be used as config"
        )
    if href.endswith(".csv"):
        df = pd.read_csv(href)
        return cast(list[dict[str, Any]], df.to_dict("records"))
    if href_is_local(href):
        with Path(href).open("r") as file:
            if href.endswith(("yaml", "yml")):
                result = yaml.safe_load(file)
            if href.endswith("json"):
                result = json.load(file)
    else:
        response = httpx.get(href, follow_redirects=True)
        response.raise_for_status()
        if href.endswith("json"):
            result = response.json()
        if href.endswith(("yaml", "yml")):
            result = yaml.safe_load(response.content.decode("utf-8"))

    if isinstance(result, dict):
        return [result]
    if isinstance(result, list):
        return result
    raise ValueError(f"Expects config to be read as a list of dictionary. Provided: {type(result)}")
