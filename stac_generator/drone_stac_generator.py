"""This module encapsulates the logic for generating STAC for the drone metadata standard."""
from datetime import datetime, timezone

import pystac
from pystac.extensions.eo import AssetEOExtension, ItemEOExtension, Band
from pystac.extensions.projection import ItemProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
import rasterio
import requests
from shapely.geometry import mapping

from stac_generator.generator import StacGenerator
from stac_generator.spatial_helpers import get_metadata_from_geotiff, EoBands

_datetime = datetime.now(timezone.utc)


class DTypeFactory:
    @staticmethod
    def get_pystac_dtype(dtype) -> DataType:
        if dtype == 'uint8':
            return DataType.UINT8
        elif dtype == 'uint16':
            return DataType.UINT16
        elif dtype == 'float32':
            return DataType.FLOAT32
        else:
            raise Exception(f'Unsupported data type {dtype}')


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
        # Get the metadata of the item.
        metadata = get_metadata_from_geotiff(location)
        data_type = DTypeFactory.get_pystac_dtype(metadata.dtype)
        datetime_utc = _datetime
        # Create the STAC asset. We are only considering the stitched MS geotiff currently.
        # Could have RGB, thumbnail, etc. in the future.
        asset = pystac.Asset(href=location, media_type=pystac.MediaType.GEOTIFF)
        # Create the STAC item and attach the assets.
        bbox = [metadata.bounds[0], metadata.bounds[1], metadata.bounds[2], metadata.bounds[3]]
        item = pystac.Item(
            id=f"item_{counter}",
            geometry=mapping(metadata.footprint),
            bbox=bbox,
            datetime=datetime_utc,
            properties={},
        )
        print(metadata)
        # Add the asset to the item.
        item.add_asset(
            key="image",
            asset=asset
        )
        # Build the data for the "projection" extension. The proj extension allows odc-stac
        # to load data without specifying particular parameters.
        proj_ext_on_item = ItemProjectionExtension.ext(item, add_if_missing=True)
        # Shape order is (y, x)
        shape = metadata.shape
        affine_transform = [rasterio.transform.from_bounds(*bbox,
                                                           shape[1], shape[0])[i]
                            for i in range(9)]
        proj_ext_on_item.apply(epsg=metadata.crs.to_epsg(), shape=list(shape),
                               transform=affine_transform)

        # Build the data for the "eo" extension.
        eo_ext_on_item = ItemEOExtension.ext(item, add_if_missing=True)
        eo_ext_on_asset = AssetEOExtension.ext(asset)
        red_eo_band = Band.create(name="red",
                                  common_name=EoBands.RED.name.lower(),
                                  description=Band.band_description("red"),
                                  center_wavelength=EoBands.RED.value)
        blue_eo_band = Band.create(name="blue",
                                   common_name=EoBands.BLUE.name.lower(),
                                   description=Band.band_description("blue"),
                                   center_wavelength=EoBands.BLUE.value)
        green_eo_band = Band.create(name="green",
                                    common_name=EoBands.GREEN.name.lower(),
                                    description=Band.band_description("green"),
                                    center_wavelength=EoBands.GREEN.value)
        nir_eo_band = Band.create(name="nir",
                                  common_name=EoBands.NIR.name.lower(),
                                  description=Band.band_description("nir"),
                                  center_wavelength=EoBands.NIR.value)
        rededge_eo_band = Band.create(name="rededge",
                                      common_name=EoBands.REDEDGE.name.lower(),
                                      description=Band.band_description("rededge"),
                                      center_wavelength=EoBands.REDEDGE.value)
        ndvi_eo_band = Band.create(name="ndvi",
                                   common_name="ndvi",
                                   description=Band.band_description("ndvi"),
                                   center_wavelength=0.55)
        ndvi2_eo_band = Band.create(name="ndvi2",
                                    common_name="ndvi2",
                                    description=Band.band_description("ndvi2"),
                                    center_wavelength=0.55)
        # Lidar does not belong in eo, electromagnetic only.
        # lidar_eo_band = Band.create(name="lidar", common_name="lidar", description="")

        # Build the data for the "raster" extension. The raster extension must be present for
        # odc-stac to be able to load data from a multi-band tiff asset. Raster does not have
        # an item level class so add to extensions with asset instead.
        raster_ext_on_asset = AssetRasterExtension.ext(asset, add_if_missing=True)
        red_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        blue_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        green_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        nir_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        rededge_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        ndvi_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        ndvi2_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        lidar_raster_band = RasterBand.create(nodata=0, data_type=data_type)
        # Bands in "raster" extension examples have name but this does not seem present in
        # RasterBand class. It works using names from "eo".

        # Need to be explicit whether fields are to be added to the asset, item or collection.
        # Each asset should specify its own band object. If the individual bands are repeated
        # in different assets they should all use the same values and include the optional 'name'
        # field to enable clients to combine and summarise the bands.
        if metadata.bands_count == 7:
            all_eo_bands = [red_eo_band, green_eo_band, blue_eo_band, nir_eo_band, rededge_eo_band,
                            ndvi_eo_band, ndvi2_eo_band]
            all_raster_bands = [red_raster_band, green_raster_band, blue_raster_band,
                                nir_raster_band, rededge_raster_band, ndvi_raster_band,
                                ndvi2_raster_band]
        elif metadata.bands_count == 3:
            all_eo_bands = [red_eo_band, green_eo_band, blue_eo_band]
            all_raster_bands = [red_raster_band, green_raster_band, blue_raster_band]
        elif metadata.bands_count == 1:
            all_eo_bands = []
            all_raster_bands = [lidar_raster_band]
        else:
            raise ValueError(f"Bands count must be 1, 3 or 7. Got {metadata.bands_count}")
        # TODO: Investigate how the order of bands is mapped.
        eo_ext_on_item.apply(bands=all_eo_bands, cloud_cover=0.0, snow_cover=0.0)
        eo_ext_on_asset.apply(bands=all_eo_bands)
        raster_ext_on_asset.apply(bands=all_raster_bands)
        return item

    def write_items_to_api(self) -> None:
        if self.items and self.collection:
            api_items_url = f"{self.base_url}/collections/{self.collection.id}/items"
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
        # self.generate_catalog()
        collection_id = "uq_gilbert_fixed_proj"
        description = "Gilbert site with correct projection."
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
        api_collections_url = f"{self.base_url}/collections"
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
