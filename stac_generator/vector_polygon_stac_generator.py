import os
import zipfile
import pystac
import fiona
from shapely.geometry import mapping
from datetime import datetime
from pystac.extensions.projection import ItemProjectionExtension
from typing import List
from generator import StacGenerator


class VectorPolygonStacGenerator(StacGenerator):
    """STAC generator for vector polygon data."""

    def __init__(self, data_type, geojson_file, zip_file, output_dir) -> None:
        super().__init__(data_type, geojson_file, zip_file)
        self.output_dir = output_dir  # Directory where STAC files will be saved
        os.makedirs(self.output_dir, exist_ok=True)

    def validate_data(self) -> bool:
        """Validate the structure of the provided data file."""
        # TODO : Validate the structure of the provided data file (this is dummy)
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def extract_shapefile_from_zip(self, zip_file_path: str, extract_to: str) -> str:
        """Extract the shapefile from the ZIP archive and return the path to the .shp file."""
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

        # Return the path to the extracted shapefile
        for file in os.listdir(extract_to):
            if file.endswith(".shp"):
                return os.path.join(extract_to, file)
        raise FileNotFoundError("No shapefile found in the zip archive.")

    def generate_item(self, location: str, counter: int) -> pystac.Item:
        """Generate a STAC item from a vector polygon file."""
        # Read the vector file (shapefile, geojson) using Fiona
        with fiona.open(location) as src:
            crs = src.crs
            bbox = src.bounds
            geometries = [feature['geometry'] for feature in src]
            geometry = mapping(geometries[0]) if geometries else None

        # Create the STAC item
        item_id = f"{self.data_type}_item_{counter}"
        item = pystac.Item(
            id=item_id,
            geometry=geometry,
            bbox=[bbox[0], bbox[1], bbox[2], bbox[3]],
            datetime=datetime.now(),
            properties={}
        )

        # Apply Projection Extension
        proj_ext = ItemProjectionExtension.ext(item, add_if_missing=True)
        proj_ext.epsg = crs['init'].split(':')[-1] if 'init' in crs else None
        proj_ext.bbox = [bbox[0], bbox[1], bbox[2], bbox[3]]

        # Add asset (assume GeoJSON or Shapefile based on location file extension)
        asset = pystac.Asset(
            href=location,
            media_type=pystac.MediaType.GEOJSON if location.endswith('.geojson') else 'application/x-shapefile',
            roles=["data"],
            title="Vector Polygon Data"
        )
        item.add_asset("data", asset)

        # Save the STAC item to a file
        item_path = os.path.join(self.output_dir, f"{item_id}_stac.json")
        item.save_object(dest_href=item_path)
        print(f"STAC Item saved to {item_path}")

        # Add to items list
        self.items.append(item)
        return item

    def generate_collection(self) -> pystac.Collection:
        """Generate a STAC collection for the vector polygon data."""
        spatial_extent = pystac.SpatialExtent([item.bbox for item in self.items])
        temporal_extent = pystac.TemporalExtent([[datetime.now(), None]])

        # Create collection
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
        collection_path = os.path.join(self.output_dir, f"{self.data_type}_collection.json")
        self.collection.save_object(dest_href=collection_path)
        print(f"STAC Collection saved to {collection_path}")
        
        return self.collection

    def generate_catalog(self) -> pystac.Catalog:
        """Generate a STAC catalog for the vector polygon data."""
        self.catalog = pystac.Catalog(
            id=f"{self.data_type}_catalog",
            description=f"STAC Catalog for {self.data_type} data"
        )

        # Add items to the catalog
        for item in self.items:
            self.catalog.add_item(item)

        # Save the catalog to a file
        catalog_path = os.path.join(self.output_dir, f"{self.data_type}_catalog.json")
        self.catalog.save_object(dest_href=catalog_path)
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
