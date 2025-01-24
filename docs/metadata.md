## Data Types

`stac_generator` classifies assets into `raster`, `vector`, and `point` data, using terminologies consistent with common [GIS](https://gisgeography.com/spatial-data-types-vector-raster/#:~:text=Vector%20data%20expresses%20by%20point,2021%20at%208%3A14%20pm) softwares. In general:

- Point data contains one or more entries where each entry has the `X` and `Y` fields describing the location. Each entry usually contains other fields describing the attributes at the point location. For instance, this can be soil sample measurements or raw instrument readings at a particular coordinate. Point data can also have a field representing depth/elevation or time.
- Vector data contains a collection of points whose relationship is determined by the vector type - (point, multipoint, line, multiline, polygon, multipolygon, etc). Vector data are usually shape files describing a plot or a field boundary, but can also contain plot level attributes - i.e. mean elevation, mean temperature, cumulative rainfall, etc.
- Raster data contains several 2D layers (called bands) where each band represents the attribute value at each (x, y) coordinate in the 2D grid. For instance, an orthomosaic contains RGB bands, where each band is a 2D matrix with value between 0 and 255.

### Supported Formats for data assets:
- Raster:
    - tif
    - geotif
- Vector:
    - shp
    - geojson
    - zip+shp
    - geopkg
- Point:
    - csv
    - txt

Note that in some cases, plot or field level attributes are recorded in a csv that does not contain X and Y columns but a plot or field ID column referencing the same attribute in a separate vector file. In this particular example, the csv should be treated as a vector rather than a point data. We have also provided a [utility tool]() (To be added) to denormalise the vector/csv combination into a single vector file.

## Collection metadata

Aside from `datetime`, `start_datetime`, `end_datetime`, collection metadata contains fields described in [STAC Common Metadata](https://github.com/radiantearth/stac-spec/blob/master/commons/common-metadata.md). In general, the most important fields are `id` (required), `keywords` (optional - can be useful for catalog filtering feature in the future), `license` (optional - licensing information).

For a more detailed list of all fields, their data types, and default values, please refer to `STACCollectionConfig` under [this](schema.md) link.

## Item metadata

Item metadata contains all fields in collection metadata and additional required `collection_date` and `collection_time` fields describing when the item was collected. Item metadata must also specify the `location` field, that points to where the data asset is stored.

For a more detailed list of all fields, their data types, and default values, please refer to `STACItemConfig` and `SourceConfig` under [this](schema.md) link.

### Point metadata

Point metadata contains all fields in item metadata (inherits from `SourceConfig`) and contains additional fields specifying how to process the given csv/txt file. This includes the `X` and `Y` fields specifying the columns to be treated as the X and Y coordinates, the `epsg` code specifying the CRS of the XY coordinates, and if the csv contains columns to be treated as depth/elevation or time, the optional `Z`, `T` and `time_format` fields.

Users should also specify useful columns under `column_info` (please see `ColumnInfo` and `HasColumnInfo` under [this](schema.md) link). For a more detailed list of all fields, their data types, and default values, please refer to `CSVConfig` under [this](extensions/point/schema.md) link.

### Vector metadata

Vector metadata contains all fields in item metadata (inherits from `SourceConfig`). Since vector data is often self-described, vector metadata only requires the `epsg` code for sanity checking - i.e. to ensure that users know whether they are providing the right asset. If the vector data is a compressed zip file with multiple shp files, a `layer` field is needed to specify which `shp` file in the zip package the metadata is describing. If the vector data contains plot or field level attributes, the `column_info` should also be used.

Users should also specify useful columns under `column_info` (please see `ColumnInfo` and `HasColumnInfo` under [this](schema.md) link). For a more detailed list of all fields, their data types, and default values, please refer to `VectorConfig` under [this](extensions/vector/schema.md) link.

### Raster metadata

Raster metadata contains all fields in item metadata (inherits from `SourceConfig`). The only extra fields in raster metadata are `epsg` code and `band_info`.

For a more detailed list of all fields, their data types, and default values, please refer to `RasterConfig` under [this](extensions/raster/schema.md) link.

## Representing Item metadata in a separate metadata file

Item metadata can be provided as entry/row in the metadata to be provided in the CLI. Please refer to [case studies](case_studies.md) for more examples.
