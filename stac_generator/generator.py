"""This module encapsulates the logic for generating STAC catalogs for a given metadata standard."""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

import pystac
from shapely.geometry import Polygon, mapping


class StacGenerator(ABC):
    """STAC generator base class."""
    def __init__(self, data_type, data_file) -> None:
        self.data_type = data_type
        self.data_file = data_file
        self.standard_file = f"./standards/{self.data_type}_standard.csv"

    def read_standard(self) -> str:
        """Open the standard definition file and return the contents as a string."""
        with open(self.standard_file, encoding='utf-8') as f:
            standard = f.readline().strip("\n")
            return standard

    @abstractmethod
    def validate_data(self) -> bool:
        """Validate the structure of the provided schema implementation matches the expected."""
        raise NotImplementedError

    @abstractmethod
    def generate(self):
        """Generate a STAC catalog for the provided metadata implementation."""
        raise NotImplementedError

    @abstractmethod
    def validate_stac(self):
        """Check that the generated STAC is valid."""
        raise NotImplementedError


class DroneStacGenerator(StacGenerator):
    """STAC generator for drone data."""
    def __init__(self, data_file) -> None:
        super().__init__("drone", data_file)

    def validate_data(self) -> bool:
        with open(self.data_file, encoding='utf-8') as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def generate(self):
        # Create the STAC catalog.
        catalog = pystac.Catalog(
            id="test_catalog", description="This is a test catalog."
        )
        location = "s3://example.com"
        # Get the bounding box of the item.
        bbox = [0, 0, 1, 1]
        footprint = Polygon([[0, 0], [0, 1], [1, 0], [1, 1], [0, 0]])
        # Create the STAC item.
        datetime_utc = datetime.now()
        item = pystac.Item(
            id="test_item_1",
            geometry=mapping(footprint),
            bbox=bbox,
            datetime=datetime_utc,
            properties={},
        )
        # Add the item to the catalog.
        catalog.add_item(item)
        item.add_asset(
            key="image",
            asset=pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF),
        )
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs((Path(tmp_dir.name) / "stac").name)

        print("Catalog HREF: ", catalog.get_self_href())
        print("Item HREF: ", item.get_self_href())

    def validate_stac(self):
        pass


class SensorStacGenerator(StacGenerator):
    """STAC generator for sensor data."""
    def __init__(self, data_file) -> None:
        super().__init__("sensor", data_file)

    def validate_data(self) -> bool:
        return False

    def generate(self):
        pass

    def validate_stac(self):
        pass
