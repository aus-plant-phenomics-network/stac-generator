import pystac_client
from odc.geo.geobox import GeoBox
from odc.stac import stac_load
# import rioxarray


if __name__ == "__main__":
    client = pystac_client.Client.open("http://localhost:8082/")
    col_id = "proj_with_transform"
    query = client.search(
        collections=[col_id]
    )
    items = query.items()
    # crs = "epsg:4326"
    # bbox = (116.96640192684013, -31.930819693348617, 116.96916478816145, -31.929350481993794)
    # geobox = GeoBox.from_bbox(bbox, shape=(3256, 5223))
    xx = stac_load(
        items,
        # bands=["red", "blue", "green", "nir"],
        # geobox=geobox,
        # resampling="rms"
        # crs=crs
        # resolution=.000001
    )
    pass
    # ds = rioxarray.open_rasterio("/Users/joseph/data/wa_uav_sample/assets/first-300-orthophoto.tif")
    # pass