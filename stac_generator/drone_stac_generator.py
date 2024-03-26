"""This module encapsulates the logic for generating STAC for the drone metadata standard."""
from datetime import datetime

import pystac
import requests
from pystac.extensions.eo import EOExtension, Band

from stac_generator.generator import StacGenerator
from stac_generator.spatial_helpers import get_bbox_and_footprint


class DroneStacGenerator(StacGenerator):
    """STAC generator for drone data."""

    def __init__(self, data_file, location_file) -> None:
        # EOExtension.enable_extension()
        super().__init__("drone", data_file, location_file)
        self.validate_data()
        with open(self.location_file, encoding="utf-8") as locations:
            counter = 0
            for line in locations:
                counter += 1
                location = line.strip("\n")
                self.items.append(self.generate_item(location, counter))
        self.generate_collection()
        self.validate_stac()

    def validate_data(self) -> bool:
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def generate_item(self, location: str, counter: int) -> pystac.Item:
        # Create a STAC item.
        # Get the bounding box of the item.
        bbox, footprint = get_bbox_and_footprint(location)
        # Create the STAC item.
        datetime_utc = datetime.now()
        asset = pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF)
        eo_ext_on_asset = EOExtension.ext(asset)
        red_band = Band.create(name="R1", common_name="red", description="",
                               center_wavelength=0.65)
        blue_band = Band.create(name="B", common_name="blue", description="",
                                center_wavelength=0.47)
        green_band = Band.create(name="G1", common_name="green", description="",
                                 center_wavelength=0.55)
        nir_band = Band.create(name="NIR1", common_name="nir", description="",
                               center_wavelength=0.87)
        # Need to be explicit whether fields are to be added to the asset, item or collection.
        # Each asset should specify its own band object. If the individual bands are repeated
        # in different assets they should all use the same values and include the optional 'name'
        # field to enable clients to combine and summarise the bands.
        all_bands = [red_band, blue_band, green_band, nir_band]
        eo_ext_on_asset.apply(bands=all_bands)

        item = pystac.Item(
            id=f"test_item_with_eo_{counter}",
            geometry=footprint,
            bbox=bbox,
            datetime=datetime_utc,
            properties={},
        )
        # Add the asset to the item.
        item.add_asset(
            key="image",
            asset=asset
        )
        eo_ext = EOExtension.ext(item, add_if_missing=True)
        eo_ext.apply(bands=all_bands, cloud_cover=0.0, snow_cover=0.0)

        return item

    def write_items_to_api(self) -> None:
        # TODO: Item post to API should not sit within the generator.
        # TODO: Refactor to appropriate location when determined.
        if self.items and self.collection:
            api_items_url = f"http://localhost:8082/collections/{self.collection.id}/items"
            for item in self.items:
                requests.post(api_items_url, json=item.to_dict())
        else:
            return

    def generate_catalog(self) -> pystac.Catalog:
        # Create the STAC catalog.
        catalog = pystac.Catalog(id="test_catalog", description="This is a test catalog.")
        for item in self.items:
            catalog.add_item(item)
        # Save the catalog to disk.
        test_dir = "./tests/stac"
        catalog.normalize_hrefs(test_dir)
        catalog.save(catalog_type=pystac.CatalogType.SELF_CONTAINED)
        self.catalog = catalog
        return self.catalog

    def generate_collection(self) -> pystac.Collection:
        self.generate_catalog()
        collection_id = "test_col_refactor"
        description = "Test Collection showing the inclusion of the 'eo' extension."
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
        self.collection = collection

        for item in self.items:
            collection.add_item(item)
        test_dir = "./tests/stac"
        collection.normalize_hrefs(test_dir)
        return self.collection

    def write_collection_to_api(self) -> None:
        # TODO: Build URL from components rather than hardcode here.
        api_collections_url = "http://localhost:8082/collections"
        if self.collection:
            requests.post(api_collections_url, json=self.collection.to_dict())

    def write_to_api(self) -> None:
        self.write_collection_to_api()
        self.write_items_to_api()

    def validate_stac(self) -> bool:
        if self.catalog:
            if self.catalog.validate():
                return True
        return False

