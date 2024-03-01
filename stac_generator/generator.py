"""This module encapsulates the logic for generating STAC catalogs for a given metadata standard."""
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Optional

import pystac
from shapely.geometry import Polygon, mapping


class StacGenerator(ABC):
    """STAC generator base class."""

    def __init__(self, data_type, data_file, location_file) -> None:
        self.data_type = data_type
        self.data_file = data_file
        self.location_file = location_file
        self.schema_file = f"./schemas/{self.data_type}_schema.csv"
        self.catalog: Optional[pystac.Catalog] = None

    def read_standard(self) -> str:
        """Open the standard definition file and return the contents as a string."""
        with open(self.schema_file, encoding="utf-8") as f:
            standard = f.readline().strip("\n")
            return standard

    @abstractmethod
    def validate_data(self) -> bool:
        """Validate the structure of the provided schema implementation matches the expected."""
        raise NotImplementedError

    @abstractmethod
    def generate(self) -> pystac.Catalog:
        """Generate a STAC catalog for the provided metadata implementation."""
        raise NotImplementedError

    @abstractmethod
    def validate_stac(self):
        """Check that the generated STAC is valid."""
        raise NotImplementedError


class DroneStacGenerator(StacGenerator):
    """STAC generator for drone data."""

    def __init__(self, data_file, location_file) -> None:
        super().__init__("drone", data_file, location_file)

    def validate_data(self) -> bool:
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def generate(self) -> pystac.Catalog:
        # Create the STAC catalog.
        catalog = pystac.Catalog(id="test_catalog", description="This is a test catalog.")
        with open(self.location_file, encoding="utf-8") as locations:
            counter = 0
            for line in locations:
                counter += 1
                location = line.strip("\n")
                # Get the bounding box of the item.
                bbox = [0.0, 0.0, 1.0, 1.0]
                footprint = Polygon(
                    [[bbox[0], bbox[1]], [bbox[0], bbox[3]], [bbox[2], bbox[3]], [bbox[2], bbox[1]]]
                )
                # Create the STAC item.
                datetime_utc = datetime.now()
                item = pystac.Item(
                    id=f"test_item_{counter}",
                    geometry=mapping(footprint),
                    bbox=bbox,
                    datetime=datetime_utc,
                    properties={},
                )
                # Add the item to the catalog.
                item.add_asset(
                    key="image",
                    asset=pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF),
                )
                catalog.add_item(item)
        # Save the catalog to disk.
        with TemporaryDirectory() as tmp_dir:
            catalog.normalize_hrefs(str(Path(tmp_dir) / "stac"))
            catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
        self.catalog = catalog
        return self.catalog

    def validate_stac(self) -> bool:
        if self.catalog:
            if self.catalog.validate():
                return True
        return False


class SensorStacGenerator(StacGenerator):
    """STAC generator for sensor data."""

    def __init__(self, data_file, location_file) -> None:
        super().__init__("sensor", data_file, location_file)

    def validate_data(self) -> bool:
        raise NotImplementedError

    def generate(self) -> pystac.Catalog:
        raise NotImplementedError

    def validate_stac(self):
        raise NotImplementedError


class StacGeneratorFactory:
    @staticmethod
    def get_stac_generator(data_type, data_file, location_file) -> StacGenerator:
        # Get the correct type of generator depending on the data type.
        if data_type == "drone":
            return DroneStacGenerator(data_file, location_file)
        elif data_type == "sensor":
            return SensorStacGenerator(data_file, location_file)
        else:
            raise Exception(f"{data_type} is not a valid data type.")
