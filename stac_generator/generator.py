"""This module encapsulates the logic for generating STAC catalogs for a given metadata standard."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from pyproj import Transformer
import pystac
import requests
import rasterio
from shapely.geometry import Polygon, mapping
from shapely.ops import transform


class StacGenerator(ABC):
    """STAC generator base class."""

    def __init__(self, data_type, data_file, location_file) -> None:
        self.data_type = data_type
        self.data_file = data_file
        self.location_file = location_file
        self.standard_file = f"./standards/{self.data_type}_standard.csv"
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

    @staticmethod
    @abstractmethod
    def generate_item(location: str, counter: int) -> pystac.Item:
        """Generate a STAC item from the provided file."""
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
    def validate_stac(self):
        """Check that the generated STAC is valid."""
        raise NotImplementedError


class DroneStacGenerator(StacGenerator):
    """STAC generator for drone data."""
    # TODO: Consider eo stac extension for drone catalog

    def __init__(self, data_file, location_file) -> None:
        super().__init__("drone", data_file, location_file)

    def validate_data(self) -> bool:
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    @staticmethod
    def generate_item(location: str, counter: int) -> pystac.Item:
        # Create a STAC item.
        # Get the bounding box of the item.
        bbox, footprint = get_bbox_and_footprint(location)
        # Create the STAC item.
        datetime_utc = datetime.now()
        item = pystac.Item(
            id=f"test_item_{counter}",
            geometry=footprint,
            bbox=bbox,
            datetime=datetime_utc,
            properties={},
        )
        # Add the item to the catalog.
        item.add_asset(
            key="image",
            asset=pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF),
        )
        # TODO: Item post to API should not sit within the generator.
        # TODO: Refactor to appropriate location when determined.
        api_items_url = "http://localhost:8082/collections/test_collection/items"
        requests.post(api_items_url, json=item.to_dict())

        return item

    def generate_catalog(self) -> pystac.Catalog:
        # Create the STAC catalog.
        catalog = pystac.Catalog(id="test_catalog", description="This is a test catalog.")
        with open(self.location_file, encoding="utf-8") as locations:
            counter = 0
            for line in locations:
                counter += 1
                location = line.strip("\n")
                item = self.generate_item(location, counter)
                catalog.add_item(item)
        # Save the catalog to disk.
        test_dir = "./tests/stac"
        catalog.normalize_hrefs(test_dir)
        catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
        self.catalog = catalog
        return self.catalog

    def generate_collection(self) -> pystac.Collection:
        collection_id = "test_collection"
        description = "Test Collection"
        # TODO: Magic bbox below, must read from data.
        # TODO: Spatial extent for collection is union of bboxes of items inside.
        spatial_extent = pystac.SpatialExtent([[116.96640192684013,
                                                -31.930819693348617,
                                                116.96916478816145,
                                                -31.929350481993794]])
        # TODO: Magic time range below, must read from data. Temporal extent is first and last
        temporal_extent = pystac.TemporalExtent([[datetime(2020, 1, 1), None]])
        extent = pystac.Extent(spatial_extent, temporal_extent)
        lic = "CC-BY-4.0"

        collection = pystac.Collection(id=collection_id,
                                       description=description,
                                       extent=extent,
                                       license=lic)
        with open(self.location_file, encoding="utf-8") as locations:
            counter = 0
            for line in locations:
                counter += 1
                location = line.strip("\n")
                item = self.generate_item(location, counter)
                collection.add_item(item)
        self.collection = collection
        return self.collection

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

    @staticmethod
    def generate_item(location: str, counter: int) -> pystac.Item:
        raise NotImplementedError

    def generate_catalog(self) -> pystac.Catalog:
        raise NotImplementedError

    def generate_collection(self) -> pystac.Collection:
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


# TODO: Move this function to general spatial helper methods.
def get_bbox_and_footprint(raster):
    with rasterio.open(raster) as r:
        bounds = r.bounds
        # Reproject the bbox to WGS84
        transformer = Transformer.from_crs(r.crs, "EPSG:4326", always_xy=True)
        # wgs84_bbox = transform(transformer.transform, bounds)
        footprint = Polygon([
            [bounds.left, bounds.bottom],
            [bounds.left, bounds.top],
            [bounds.right, bounds.top],
            [bounds.right, bounds.bottom]
        ])
        wgs84_footprint = transform(transformer.transform, footprint)
        wgs84_bounds = wgs84_footprint.bounds
        wgs_84_bbox = [wgs84_bounds[0], wgs84_bounds[1], wgs84_bounds[2], wgs84_bounds[3]]
        return wgs_84_bbox, mapping(wgs84_footprint)
