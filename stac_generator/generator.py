"""This module encapsulates the logic for generating STAC for a given metadata standard."""
from abc import ABC, abstractmethod
import os
from typing import List, Optional

import pystac


class StacGenerator(ABC):
    """STAC generator base class."""

    def __init__(self, data_type, data_file, location_file) -> None:
        self.base_url = os.environ.get("STAC_API_URL", None)
        if self.base_url is None:
            raise ValueError("Environment variable STAC_API_URL must be defined.")
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
        """Generate a STAC item from the provided file."""
        raise NotImplementedError

    @abstractmethod
    def write_items_to_api(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def generate_catalog(self) -> pystac.Catalog:
        """Generate a STAC catalog for the provided metadata implementation."""
        raise NotImplementedError

    @abstractmethod
    def generate_collection(self) -> pystac.Collection:
        """Generate a STAC collection for the provided metadata implementation."""
        raise NotImplementedError

    @abstractmethod
    def write_collection_to_api(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def write_to_api(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def validate_stac(self) -> bool:
        """Check that the generated STAC is valid."""
        raise NotImplementedError
