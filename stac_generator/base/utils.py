import json
import logging
import urllib.parse
from pathlib import Path
from typing import Any, cast

import httpx
import pandas as pd
import yaml

SUPPORTED_URI_SCHEMES = ["http", "https"]
logger = logging.getLogger(__name__)


def parse_href(base_url: str, collection_id: str, item_id: str | None = None) -> str:
    """Generate href for collection or item based on id

    :param base_url: path to catalog.
    :type base_url: str
    :param collection_id: collection id
    :type collection_id: str
    :param item_id: item id, defaults to None
    :type item_id: str | None, optional
    :return: uri to collection or item
    :rtype: str
    """
    if item_id:
        return urllib.parse.urljoin(base_url, f"{collection_id}/{item_id}")
    return urllib.parse.urljoin(base_url, f"{collection_id}")


def href_is_stac_api_endpoint(href: str) -> bool:
    """Check if href points to a resource behind a stac api

    :param href: path to resource
    :type href: str
    :return: local or non-local
    :rtype: bool
    """
    output = urllib.parse.urlsplit(href)
    return output.scheme == ""


def force_write_to_stac_api(url: str, id: str, json: dict[str, Any]) -> None:
    """Force write a json object to a stac api endpoint.
    This function will try sending a POST request and if a 409 error is encountered,
    try sending a PUT request. Other exceptions if occured will be raised

    :param url: path to stac resource for creation/update
    :type url: str
    :param json: json object
    :type json: dict[str, Any]
    """
    try:
        logger.debug(f"sending POST request to {url}")
        response = httpx.post(url=url, json=json)
        response.raise_for_status()
    except httpx.HTTPStatusError as err:
        if err.response.status_code == 409:
            logger.debug(f"sending PUT request to {url}")
            response = httpx.put(url=f"{url}/{id}", json=json)
            response.raise_for_status()
        else:
            raise err


def read_source_config(href: str) -> list[dict[str, Any]]:
    logger.debug(f"reading config file from {href}")
    if not href.endswith(("json", "yaml", "yml", "csv")):
        raise ValueError(
            "Unsupported extension. We currently allow json/yaml/csv files to be used as config"
        )
    if href.endswith(".csv"):
        df = pd.read_csv(href)
        return cast(list[dict[str, Any]], df.to_dict("records"))
    if not href.startswith(("http", "https")):
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
