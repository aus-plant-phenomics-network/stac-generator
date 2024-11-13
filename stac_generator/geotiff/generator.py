import pystac
import rasterio
from pystac.extensions.eo import AssetEOExtension, Band, ItemEOExtension
from pystac.extensions.projection import ItemProjectionExtension
from pystac.extensions.raster import AssetRasterExtension, DataType, RasterBand
from shapely.geometry import mapping

from stac_generator.base.generator import ItemGenerator
from stac_generator.geotiff.schema import GeoTiffConfig
from stac_generator.geotiff.utils import EoBands, get_metadata_from_geotiff


class GeoTiffGenerator(ItemGenerator[GeoTiffConfig]):
    """Stac generator for drone data."""

    def create_item_from_config(self, source_cfg: GeoTiffConfig) -> pystac.Item:
        metadata = get_metadata_from_geotiff(source_cfg.location)
        data_type = DataType(metadata.dtype)
        bbox = [metadata.bounds[0], metadata.bounds[1], metadata.bounds[2], metadata.bounds[3]]
        # Create the Stac asset. We are only considering the stitched MS geotiff currently.
        # Could have RGB, thumbnail, etc. in the future.
        asset = pystac.Asset(href=source_cfg.location, media_type=pystac.MediaType.GEOTIFF)
        item = pystac.Item(
            id=source_cfg.id,
            geometry=mapping(metadata.footprint),
            bbox=bbox,
            assets={"image": asset},
            datetime=source_cfg.datetime,
            start_datetime=source_cfg.start_datetime,
            end_datetime=source_cfg.end_datetime,
            properties={},
        )
        proj_ext_on_item = ItemProjectionExtension.ext(item, add_if_missing=True)
        # Shape order is (y, x)
        shape = metadata.shape
        affine_transform = [
            rasterio.transform.from_bounds(*bbox, shape[1], shape[0])[i] for i in range(9)
        ]
        proj_ext_on_item.apply(
            epsg=metadata.crs.to_epsg(), shape=list(shape), transform=affine_transform
        )

        # Build the data for the "eo" extension.
        eo_ext_on_item = ItemEOExtension.ext(item, add_if_missing=True)
        eo_ext_on_asset = AssetEOExtension.ext(asset)
        red_eo_band = Band.create(
            name="red",
            common_name=EoBands.RED.name.lower(),
            description=Band.band_description("red"),
            center_wavelength=EoBands.RED.value,
        )
        blue_eo_band = Band.create(
            name="blue",
            common_name=EoBands.BLUE.name.lower(),
            description=Band.band_description("blue"),
            center_wavelength=EoBands.BLUE.value,
        )
        green_eo_band = Band.create(
            name="green",
            common_name=EoBands.GREEN.name.lower(),
            description=Band.band_description("green"),
            center_wavelength=EoBands.GREEN.value,
        )
        nir_eo_band = Band.create(
            name="nir",
            common_name=EoBands.NIR.name.lower(),
            description=Band.band_description("nir"),
            center_wavelength=EoBands.NIR.value,
        )
        rededge_eo_band = Band.create(
            name="rededge",
            common_name=EoBands.REDEDGE.name.lower(),
            description=Band.band_description("rededge"),
            center_wavelength=EoBands.REDEDGE.value,
        )
        ndvi_eo_band = Band.create(
            name="ndvi",
            common_name="ndvi",
            description=Band.band_description("ndvi"),
            center_wavelength=0.55,
        )
        ndvi2_eo_band = Band.create(
            name="ndvi2",
            common_name="ndvi2",
            description=Band.band_description("ndvi2"),
            center_wavelength=0.55,
        )
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
            all_eo_bands = [
                red_eo_band,
                green_eo_band,
                blue_eo_band,
                nir_eo_band,
                rededge_eo_band,
                ndvi_eo_band,
                ndvi2_eo_band,
            ]
            all_raster_bands = [
                red_raster_band,
                green_raster_band,
                blue_raster_band,
                nir_raster_band,
                rededge_raster_band,
                ndvi_raster_band,
                ndvi2_raster_band,
            ]
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
