"""This module encapsulates the logic for generating STAC for the drone metadata standard."""
from datetime import datetime

import pystac
import rasterio
import requests
from pystac.extensions.eo import AssetEOExtension, ItemEOExtension, Band
from pystac.extensions.projection import ItemProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand

from stac_generator.generator import StacGenerator
from stac_generator.spatial_helpers import get_bbox_and_footprint


class DroneStacGenerator(StacGenerator):
    """STAC generator for drone data."""

    def __init__(self, data_file, location_file) -> None:
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
        # Get the bounding box of the item.
        bbox, footprint = get_bbox_and_footprint(location)
        # Create the STAC asset. We are only considering the stitched MS geotiff currently.
        # Could have RGB, thumbnail, etc. in the future.
        datetime_utc = datetime.now()
        asset = pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF)
        # Create the STAC item and attach the assets.
        item = pystac.Item(
            id=f"multiple_assets_{counter}",
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
        # Build the data for the "projection" extension. The proj extension allows odc-stac
        # to load data without specifying particular parameters.
        proj_ext_on_item = ItemProjectionExtension.ext(item, add_if_missing=True)
        # Shape order is (y, x)
        # TODO: Magic tuple below, must generate from reading file in question.
        shape = [5223, 3256]
        affine_transform = [rasterio.transform.from_bounds(*bbox, shape[1], shape[0])[i]
                            for i in range(9)]
        # TODO: Get epsg code from file.
        proj_ext_on_item.apply(epsg=4326, shape=shape, transform=affine_transform)
        # Build the data for the "eo" extension.
        eo_ext_on_item = ItemEOExtension.ext(item, add_if_missing=True)
        eo_ext_on_asset = AssetEOExtension.ext(asset)
        red_eo_band = Band.create(name="R1", common_name="red", description="",
                                  center_wavelength=0.65)
        blue_eo_band = Band.create(name="B", common_name="blue", description="",
                                   center_wavelength=0.47)
        green_eo_band = Band.create(name="G1", common_name="green", description="",
                                    center_wavelength=0.55)
        nir_eo_band = Band.create(name="NIR1", common_name="nir", description="",
                                  center_wavelength=0.87)
        # Need to be explicit whether fields are to be added to the asset, item or collection.
        # Each asset should specify its own band object. If the individual bands are repeated
        # in different assets they should all use the same values and include the optional 'name'
        # field to enable clients to combine and summarise the bands.
        all_eo_bands = [red_eo_band, blue_eo_band, green_eo_band, nir_eo_band]
        eo_ext_on_item.apply(bands=all_eo_bands, cloud_cover=0.0, snow_cover=0.0)
        eo_ext_on_asset.apply(bands=all_eo_bands)
        # Build the data for the "raster" extension. The raster extension must be present for
        # odc-stac to be able to load data from a multi-band tiff asset. Raster does not have
        # an item level class so add to extensions with asset instead.
        raster_ext_on_asset = AssetRasterExtension.ext(asset, add_if_missing=True)
        red_raster_band = RasterBand.create(nodata=0, data_type=DataType.UINT16)
        blue_raster_band = RasterBand.create(nodata=0, data_type=DataType.UINT16)
        green_raster_band = RasterBand.create(nodata=0, data_type=DataType.UINT16)
        nir_raster_band = RasterBand.create(nodata=0, data_type=DataType.UINT16)
        # Bands in "raster" extension examples have name but this does not seem present in
        # RasterBand class. It works using names from "eo".
        # TODO: Investigate how the order of bands is mapped.
        all_raster_bands = [red_raster_band, blue_raster_band, green_raster_band, nir_raster_band]
        raster_ext_on_asset.apply(bands=all_raster_bands)
        return item

    def write_items_to_api(self) -> None:
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
        collection_id = "proj_with_transform"
        description = "Test Collection showing the inclusion of the 'raster' extension."
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

        self.collection = pystac.Collection(id=collection_id,
                                            description=description,
                                            extent=extent,
                                            license=lic)

        for item in self.items:
            self.collection.add_item(item)
        test_dir = "./tests/stac"
        self.collection.normalize_hrefs(test_dir)
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
            if not self.catalog.validate():
                return False
        if self.collection:
            if not self.collection.validate():
                return False
        return True
