"""This module encapsulates the logic for generating Stac for a given metadata standard."""

import os
from abc import ABC, abstractmethod
from typing import List, Optional

import pystac
import requests


class StacGenerator(ABC):
    """Stac generator base class."""

    def __init__(self, data_type, data_file, location_file, **kwargs) -> None:
        self.base_url = os.environ.get("Stac_API_URL", None)
        if self.base_url is None:
            raise ValueError("Environment variable Stac_API_URL must be defined.")
        self.data_type = data_type
        self.data_file = data_file
        self.location_file = location_file
        self.standard_file = f"./standards/{self.data_type}_standard.csv"
        self.items: List[pystac.Item] = []
        self.catalog: Optional[pystac.Catalog] = None
        self.collection: Optional[pystac.Collection] = None

    def read_standard(self) -> str:
        """Open the standard definition file and return the contents as a string."""
        with open(self.standard_file, encoding="utf-8") as f:
            standard = f.readline().strip("\n")
            return standard

    @abstractmethod
    def validate_data(self) -> bool:
        """Validate the structure of the provided schema implementation matches the expected."""
        raise NotImplementedError

    @abstractmethod
    def generate_item(self, location: str, counter: int) -> pystac.Item:
        """Generate a Stac item from the provided file."""
        raise NotImplementedError

    def write_items_to_api(self) -> None:
        if self.items and self.collection:
            api_items_url = f"{self.base_url}/collections/{self.collection.id}/items"
            for item in self.items:
                requests.post(api_items_url, json=item.to_dict())

    @abstractmethod
    def generate_catalog(self) -> pystac.Catalog:
        """Generate a Stac catalog for the provided metadata implementation."""
        raise NotImplementedError

    @abstractmethod
    def generate_collection(self) -> pystac.Collection:
        """Generate a Stac collection for the provided metadata implementation."""
        raise NotImplementedError

    def write_collection_to_api(self) -> None:
        # TODO: Build URL from components rather than hardcode here.
        api_collections_url = f"{self.base_url}/collections"
        if self.collection:
            requests.post(api_collections_url, json=self.collection.to_dict())

    def write_to_api(self) -> None:
        self.write_collection_to_api()
        self.write_items_to_api()

    def validate_stac(self) -> bool:
        if self.catalog and not self.catalog.validate():
            return False
        if self.collection and not self.collection.validate():
            return False
        return True
