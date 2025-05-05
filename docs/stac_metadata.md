[STAC](https://stacspec.org/en) (SpatioTemporal Asset Catalog) metadata refers to a standardized way of describing geospatial data, such as satellite imagery, through metadata that is human-readable and machine-readable. It follows the STAC specification, which provides a structured format for organizing and searching for spatio-temporal data.

### Core Components

- `Item`: Represents a single spatiotemporal asset (e.g., a satellite image). It includes:

    - `id`: item's id

    - `bbox`: item's bounding box.

    - `geometry`: spatial extent (e.g., a GeoJSON polygon).

    - `datetime`: specifies the temporal information (start/end dates for Collections).

    - `assets`: individual data files (e.g., GeoTIFFs) with additional metadata such as roles (e.g., thumbnail, data).

- `Collection`: a group of related Items with shared metadata, such as satellite images from the same mission.



### Extensions

STAC is extensible, allowing additional fields to describe specific domains or use cases. Common extensions include:

- [Raster Extension](https://github.com/stac-extensions/raster): describes additional raster metadata such as sampling, scale, offset etc.
- [Electro-Optical Extension](https://github.com/stac-extensions/eo): for satellite images, describing bands, cloud cover, etc.
- [Projection Extension](https://github.com/stac-extensions/projection): provides a way to describe the primary asset's coordinates referencing system (CRS). 

STAC metadata is typically stored in JSON format and is widely used in platforms and services dealing with geospatial data to improve accessibility and usability.

### Example STAC Metadata

=== "Item"

    ```json
    --8<-- "tests/files/integration_tests/point/generated/adelaide_airport/adelaide_airport.json"
    ```

=== "Collection"

    ```json
    --8<-- "tests/files/integration_tests/point/generated/collection.json"
    ```
