## Workflow

![](./images/StacGeneratorFactory.svg)

1. **I/O**

    Users provides as input various configuration formats. Configurations can be paths to json/yaml config files, python dictionaries or subclasses of `SourceConfig`.

2. **Classification/Validation**

    The configs are passed to `StacGeneratorFactory` which matches raw configurations to the appropriate configuration subclass - `RasterConfig`, `VectorConfig` and `PointConfig`. The matching process is performed using the config's `location` extension. The promotion step also involves data validation, which checks whether the required fields are provided.

3. **Conversion to ItemGenerator**

    The `SourceConfig` instances are then promoted to an appropriate `ItemGenerator` instance (`RasterGenerator`, `VectorGenerator`, and `PointGenerator`).

4. **Instantiate CollectionGenerator**

    Together with the list of `ItemGenerator` subjects, a set of collection's fields and keywords is used to instantiate the `CollectionGenerator` object.

5. **Serialisation**

    Using the `CollectionGenerator` object, the STAC generator uses the `StacSerialiser` class for writing the metadata locally or to a remote API.

## FAQ

### Handling of Collection's spatial extent attributes

The spatial extent is determined as enclosing bounding box of all items' bounding boxes. This bounding box is in WGS 84.

### Handling of Collection's temporal extent attributes

The temporal extent is determined as the minimum `start_datetime` and the maximum `end_datetime` in UTC.

### Handling of Item's geometry attributes

The item's geometry is read from the asset. If the asset's geometry is not in WGS 84 (EPSG 4326), the values are converted to WGS 84 before serialisation.

### Handling of Item's bbox attributes

An item's bounding box (top, left, bottom, right) is determined from the smallest bounding box that encloses the item's geometry. The values are converted to WGS 84 before serialisation.

### Handling of Item's datetime attributes

The item's datetime value is determined from the config's fields `collection_date`, `collection_time`, and `timezone`. If `timezone` is not provided or `timezone` is `local`, the data's timezone is inferred using the asset's geometry. The `collection_date` and `collection_time` are then combined and converted from the `timezone` value to `utc`.

### Handling of Item's start_datetime and end_datetime attributes

For asset that are time-series based (either a point asset with a `T` attribute or a joined vector asset with a `date_column` in `join_config`), the date values are extracted from the asset. Any timestamp that are not timezone-awared will be assigned a timezone value based on the `timezone` config field as described [previously](#handling-of-items-datetime-attributes). All timestamps are then converted to UTC. `start_datetime` and `end_datetime` are the minimum and maximum values of the UTC timestamps.

For assets that do not contain timeseries, `start_datetime` and `end_datetime` are assigned the value of `datetime`.

### Handling of Item's assets attributes

Unlike a generic STAC item that can contain multiple assets, a STAC Generator generated Item contains only a single asset which has the key `data`. The asset's role is also `data`.

### Handling of Item's property attributes

Each STAC Generator generated STAC Item contains an object under the key `stac_generator` in `properties`. The object is required for subsequent asset parsing in the `mccn-engine`.
