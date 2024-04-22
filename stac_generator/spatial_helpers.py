from pyproj import Transformer
import rasterio
from shapely.geometry import Polygon, mapping
from shapely.ops import transform


def get_bbox_and_footprint(raster, dummy: bool = False):
    # TODO: It is likely not best practice to open the raster multiple times to get different
    # TODO: pieces of information. Consider opening once and getting everything relevant. For
    # TODO: now this is the only case of opening the asset so it's OK.
    if dummy:
        wgs84_bbox = [116.96640192684013, -31.930819693348617,
                       116.96916478816145, -31.929350481993794]
        wgs84_footprint = Polygon([
            [wgs84_bbox[0], wgs84_bbox[1]],
            [wgs84_bbox[0], wgs84_bbox[3]],
            [wgs84_bbox[2], wgs84_bbox[3]],
            [wgs84_bbox[2], wgs84_bbox[1]]
        ])
    else:
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
            wgs84_bbox = [wgs84_bounds[0], wgs84_bounds[1], wgs84_bounds[2], wgs84_bounds[3]]
    return wgs84_bbox, mapping(wgs84_footprint)
