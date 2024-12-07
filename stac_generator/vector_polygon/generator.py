import fiona
import pandas as pd
import pystac
from pystac.extensions.projection import ItemProjectionExtension
from shapely.geometry import mapping

from stac_generator.base.generator import StacGenerator
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig

from .schema import VectorPolygonSourceConfig


class VectorPolygonGenerator(StacGenerator[VectorPolygonSourceConfig]):
    def __init__(
        self,
        source_df: pd.DataFrame,
        collection_cfg: StacCollectionConfig,
        catalog_cfg: StacCatalogConfig | None = None,
        href: str | None = None,
    ) -> None:
        super().__init__(
            source_df=source_df,
            collection_cfg=collection_cfg,
            catalog_cfg=catalog_cfg,
            href=href,
        )

    def create_item_from_config(self, source_cfg: VectorPolygonSourceConfig) -> list[pystac.Item]:
        print(source_cfg)
        if source_cfg.location.endswith(".zip"):  # ZIP archive case
            if source_cfg.location.startswith("http"):  # Remote ZIP file
                zip_path = (
                    f"zip+{source_cfg.location}"  # Use Fiona's zip+https protocol for remote files
                )
            else:  # Local ZIP file
                zip_path = (
                    f"zip://{source_cfg.location}"  # Use Fiona's zip:// protocol for local files
                )
        else:
            if source_cfg.location.startswith("http"):  # Remote non-ZIP file (GeoJSON or shapefile)
                zip_path = source_cfg.location  # Use the URL directly
            else:  # Local non-ZIP file
                zip_path = source_cfg.location  # Use the local path directly

        with fiona.open(zip_path) as src:
            crs = src.crs
            bbox = src.bounds
            geometries = [feature["geometry"] for feature in src]
            geometry = mapping(geometries[0]) if geometries else None

        # Create the STAC item
        item_id = source_cfg.prefix
        item = pystac.Item(
            id=item_id,
            geometry=geometry,
            bbox=bbox,
            datetime=source_cfg.datetime,
            start_datetime=source_cfg.start_datetime,
            end_datetime=source_cfg.end_datetime,
            properties={},
        )

        # Apply Projection Extension
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        epsg = crs.to_epsg()
        if source_cfg.epsg != epsg:
            raise ValueError(
                f"EPSG mismatch: source_cfg.epsg ({source_cfg.epsg}) does not match shapefile EPSG ({epsg})."
            )

        # Add proj:epsg to the item
        proj_ext.apply(
            epsg=epsg,
            bbox=[bbox[0], bbox[1], bbox[2], bbox[3]],
        )

        # Add asset
        asset = pystac.Asset(
            href=str(source_cfg.location),
            media_type=pystac.MediaType.GEOJSON
            if source_cfg.location.endswith(".geojson")
            else "application/x-shapefile",
            roles=["data"],
            title="Vector Polygon Data",
        )

        item.add_asset("data", asset)

        # Return the generated item
        return [item]
