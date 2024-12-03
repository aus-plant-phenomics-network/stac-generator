## About

[STAC](https://stacspec.org/en) is a metadata specification for spatial dataset. `stac_generator` is a CLI tool for building STAC compliant catalogs and collections from common spatial data extensions for raster, vector and point data.


## Install

To install the latest version of `stac_generator`, simply run

```bash
pip install stac_generator
```

## Quickstart

In the following tutorial, we will use `stac_generator` to describe a combination of set of vector data. The vector data contains LGA data in geopackage format, soil exposure as a geojson, soil subgroup as a zip compressed shape file. The generated metadata is a STAC collection with each dataset as a STAC item.

### Creating a configuration file

Some spatial data types like vector are self-describing with well-understood structure adhering to some specifications. Others like csv point data are not. As such, the `stac_generator` requires additional external metadata provided in the form of a configuration file. At the bear minimum, each entry in the configuration file must have an `id` field that corresponds to the `id` of the generated item, and a `location` field that describes where the raw data is stored. Each data type may have additional requirements for processing the raw data file. For more information, please visit the schema page for each extension in the navigation bar.

For our example, we will use the following [vector_config.json](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/documentation/vector_config.json):

```json
[
  {
    "id": "lga",
    "location": "https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/unit_tests/vector/data/lga.gpkg",
    "collection_date": "2023-04-01",
    "collection_time": "09:00:00",
    "epsg": 3857
  },
  {
    "id": "soil_exposure",
    "title": "soil exposure data - DEWNR Soil and Land Program",
    "location": "https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/unit_tests/vector/data/soil_exposure.geojson",
    "collection_date": "2016-06-09",
    "collection_time": "09:00:00",
    "epsg": 7844
  },
  {
    "id": "soil_subgroup",
    "title": "soil subgroup data - DEWNR Soil and Land Program",
    "location": "https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/unit_tests/vector/data/soil_subgroup.zip",
    "collection_date": "2016-06-09",
    "collection_time": "09:00:00",
    "epsg": 1168
  }
]

```

In this example, the raw data (shape/geojson/gpkg) files are stored in a remote location. If you have files stored locally, you can also set the `location` field to point to the raw data.

Users can also use a csv for configuration. The equivalent config in csv format can be found [here](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/documentation/vector_config.csv).

### Saving the STAC records

Once the configuration file is created, users can save the records to a local directory on disk, or to push to a STAC API endpoint.

```bash
stac_generator <config_path> --dst <save_path> --id <collection_id>
```

For instance, if I want to create the collection `vector_data` to `example/generated` with the `vector_config.json` config in the current directory, I can run the following:

```bash
stac_generator vector_config.json --dst example/generated --id vector_data
```

For saving to a remote API endpoint:

```bash
stac_generator vector_config.json --dst http://115.146.84.224:8082 --id vector_data
```
