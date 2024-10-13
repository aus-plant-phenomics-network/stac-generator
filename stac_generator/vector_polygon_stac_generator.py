import pystac
import fiona
from shapely.geometry import mapping
from datetime import datetime
from pathlib import Path
from pystac.extensions.projection import ItemProjectionExtension
from .generator import StacGenerator


class VectorPolygonStacGenerator(StacGenerator):
    """STAC generator for vector polygon data."""

    def __init__(self, data_file: str, location_file: str) -> None:
        super().__init__("vector", data_file, location_file)
        self.output_dir = Path("./tests/stac")  # Directory where STAC files will be saved
        self.generate_item(location=data_file, counter=1)
        self.generate_item(location=location_file, counter=2)
        
        # Generate collection and catalog
        self.generate_collection()
        self.generate_catalog()

        # Validate the generated STAC
        if self.validate_stac():
            print("STAC validation passed.")
        else:
            print("STAC validation failed.")
 

    def validate_data(self) -> bool:
        """Validate the structure of the provided data file."""
        # TODO : Validate the structure of the provided data file (this is dummy)
        with open(self.data_file, encoding="utf-8") as data:
            data_keys = data.readline().strip("\n")
            standard_keys = self.read_standard()
            if data_keys != standard_keys:
                raise ValueError("The data keys do not match the standard keys.")
            return True

    def generate_item(self, location: str, counter: int) -> pystac.Item:
        """Generate a STAC item from a vector polygon file.
        Handles both GeoJSON files and shapefiles inside ZIP archives"""

        # If the location is a ZIP file, handle it accordingly
        if location.endswith(".zip"):  # Assume zip shape archive
            shapefile_name = location.split('/')[-1].replace(".zip", ".shp")  # Extract .shp file name
            
            if location.startswith("http"):  # Remote file (HTTP/HTTPS)
                zip_path = f"/vsicurl/{location}/{shapefile_name}"  # Use /vsicurl/ to read from remote ZIP file
            else:  # Local file
                zip_path = f"/vsizip/{location}/{shapefile_name}"  # Use /vsizip/ to read from local ZIP file
        else:
            if location.startswith("http"):  # Remote non-ZIP file (GeoJSON or shapefile)
                zip_path = f"/vsicurl/{location}"  # Use /vsicurl/ for remote files
            else:  # Local non-ZIP file
                zip_path = location  # Use the local path directly

        # Open the vector file (GeoJSON or Shapefile) using Fiona
        with fiona.open(zip_path) as src:
            crs = src.crs
            bbox = src.bounds
            geometries = [feature['geometry'] for feature in src]
            geometry = mapping(geometries[0]) if geometries else None

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
        proj_ext.bbox = [bbox[0], bbox[1], bbox[2], bbox[3]]

        # Add asset (based on file type)
        asset = pystac.Asset(
            href=str(location),
            media_type=pystac.MediaType.GEOJSON if location.endswith(".geojson") else 'application/x-shapefile',
            roles=["data"],
            title="Vector Polygon Data"
        )
        item.add_asset("data", asset)

        # Save the STAC item to a file
        item_path = Path(self.output_dir) / f"{item_id}_stac.json"
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
        self.collection.normalize_hrefs(self.output_dir.as_posix())

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
