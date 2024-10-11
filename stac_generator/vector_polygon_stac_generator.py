import zipfile
import pystac
import fiona
from shapely.geometry import mapping
from datetime import datetime
from pathlib import Path
from pystac.extensions.projection import ItemProjectionExtension
from typing import List
from generator import StacGenerator


class VectorPolygonStacGenerator(StacGenerator):
    """STAC generator for vector polygon data."""

    def __init__(self, data_type, geojson_file, zip_file, output_dir) -> None:
        super().__init__(data_type, geojson_file, zip_file)
        self.output_dir = Path(output_dir)  # Use Path object for the output directory
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def validate_data(self) -> bool:
        """Validate the structure of the provided data file."""
        # TODO : Validate the structure of the provided data file (this is dummy)
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def generate_item(self, zip_file: str = None, shapefile_name: str = None, location: str = None, counter: int = 1) -> pystac.Item:
        """Generate a STAC item from a vector polygon file.
        Handles both GeoJSON files and shapefiles inside ZIP archives."""

        # If it's a ZIP file, use Fiona to open the shapefile inside the zip without extracting
        if zip_file and shapefile_name:
            zip_path = f"/vsizip/{zip_file}/{shapefile_name}"  # Explicitly use /vsizip/ to read from ZIP
            with fiona.open(zip_path) as src:
                crs = src.crs
                bbox = src.bounds
                geometries = [feature['geometry'] for feature in src]
                geometry = mapping(geometries[0]) if geometries else None

        # If it's a GeoJSON file, open it directly
        elif location:
            with fiona.open(location) as src:
                crs = src.crs
                bbox = src.bounds
                geometries = [feature['geometry'] for feature in src]
                geometry = mapping(geometries[0]) if geometries else None
        else:
            raise ValueError("You must provide either a location (GeoJSON) or a zip_file and shapefile_name.")

        # Create the STAC item
        item_id = f"{self.data_type}_item_{counter}"
        item = pystac.Item(
            id=item_id,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime.now(),
            properties={}
        )

        # Apply Projection Extension
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.epsg = crs['init'].split(':')[-1] if 'init' in crs else None
        proj_ext.bbox = bbox

        # Add asset (based on file type)
        asset = pystac.Asset(
            href=str(location if location else f"{zip_file}!{shapefile_name}"),
            media_type=pystac.MediaType.GEOJSON if location else 'application/x-shapefile',
            roles=["data"],
            title="Vector Polygon Data"
        )
        item.add_asset("data", asset)

        # Save the STAC item to a file
        item_path = self.output_dir / f"{item_id}_stac.json"
        item.save_object(dest_href=str(item_path))
        print(f"STAC Item saved to {item_path}")

        # Add to items list
        self.items.append(item)
        return item


    def generate_collection(self) -> pystac.Collection:
        """Generate a STAC collection for the vector polygon data."""
        
        # Calculate the combined bounding box (min_x, min_y, max_x, max_y)
        min_x = min(item.bbox[0] for item in self.items)
        min_y = min(item.bbox[1] for item in self.items)
        max_x = max(item.bbox[2] for item in self.items)
        max_y = max(item.bbox[3] for item in self.items)

        combined_bbox = [min_x, min_y, max_x, max_y]

        # Create the spatial extent using the combined bounding box
        spatial_extent = pystac.SpatialExtent([combined_bbox])
        
        # Temporal extent (can adjust as needed)
        temporal_extent = pystac.TemporalExtent([[datetime.now(), None]])

        # Create the STAC collection
        self.collection = pystac.Collection(
            id=f"{self.data_type}_collection",
            description=f"STAC Collection for {self.data_type} data",
            extent=pystac.Extent(spatial=spatial_extent, temporal=temporal_extent),
            license="CC-BY-4.0"
        )

        # Add items to the collection
        for item in self.items:
            self.collection.add_item(item)

        # Save the collection to a file
        collection_path = self.output_dir / f"{self.data_type}_collection.json"
        self.collection.save_object(dest_href=str(collection_path))
        print(f"STAC Collection saved to {collection_path}")
        
        return self.collection
    def generate_catalog(self) -> pystac.Catalog:
        """Generate a STAC catalog for the vector polygon data."""
        
        # Create the catalog
        self.catalog = pystac.Catalog(
            id=f"{self.data_type}_catalog",
            description=f"STAC Catalog for {self.data_type} data"
        )
        
        # Set the href for the catalog (self link)
        catalog_path = self.output_dir / f"{self.data_type}_catalog.json"
        self.catalog.set_self_href(str(catalog_path))  # Set the self-href for the root catalog

        # Add items to the catalog
        for item in self.items:
            self.catalog.add_item(item)

        # Ensure all links have valid href values
        for link in self.catalog.links:
            if link.href is None or link.href == "":
                raise ValueError(f"Link href cannot be None or empty. Link: {link}")
        
        # Save the catalog to a file
        self.catalog.save_object(dest_href=str(catalog_path))
        print(f"STAC Catalog saved to {catalog_path}")

        return self.catalog


    def write_items_to_api(self) -> None:
        """Write items to the STAC API."""
        if self.items and self.collection:
            api_items_url = f"{self.base_url}/collections/{self.collection.id}/items"
            for item in self.items:
                item_dict = item.to_dict()
                # Simulating the POST request
                print(f"POST {api_items_url}: {item_dict}")

    def write_collection_to_api(self) -> None:
        """Write the collection to the STAC API."""
        if self.collection:
            api_collections_url = f"{self.base_url}/collections"
            collection_dict = self.collection.to_dict()
            # Simulating the POST request
            print(f"POST {api_collections_url}: {collection_dict}")

    def write_to_api(self) -> None:
        """Write the catalog and collection to the API."""
        self.write_collection_to_api()
        self.write_items_to_api()

    def validate_stac(self) -> bool:
        """Validate the generated STAC."""
        if self.catalog and not self.catalog.validate():
            print("Catalog validation failed")
            return False
        if self.collection and not self.collection.validate():
            print("Collection validation failed")
            return False
        print("STAC validation passed")
        return True
