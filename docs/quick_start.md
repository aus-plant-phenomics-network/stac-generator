
## Raster Data



## Point Data



## Composite Data

It is not uncommon to have more than one data types in a project. To describe multiple items of different data types, we can use a combined config or we can pass all the configs to the CLI at once.

### Using a combined config

Let's say you want to describe items in `raster_simple_config.json`, `point_simple_config.json`, and `vector_simple_config.json`, an easy way is to make a `combined_config.json` with entries from all the sub configs:

<details>
<summary>JSON</summary>

```json title="combined_config.json"
[
    {
        "id": "Werribee",
        "location": "Werribee.geojson",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00"
    },
    {
        "id": "soil_data",
        "location": "soil.csv",
        "collection_date": "2020-01-01",
        "collection_time": "10:00:00",
        "X": "eastings_utm",
        "Y": "northings_utm",
        "epsg": 28355,
        "column_info": [
            {
                "name": "ca_soln",
                "description": "Calcium solution in ppm"
            },
            {
                "name": "profile",
                "description": "Field profile"
            }
        ]
    },
    {
        "id": "L2A_PVI",
        "location": "L2A_PVI.tif",
        "collection_date": "2021-02-21",
        "collection_time": "10:00:17",
        "band_info": [
            {
                "name": "B04",
                "common_name": "red",
                "description": "Common name: red, Range: 0.6 to 0.7",
                "wavelength": 0.6645
            },
            {
                "name": "B03",
                "common_name": "green",
                "description": "Common name: green, Range: 0.5 to 0.6",
                "wavelength": 0.56
            },
            {
                "name": "B02",
                "common_name": "blue",
                "description": "Common name: blue, Range: 0.45 to 0.5",
                "wavelength": 0.4966
            }
        ]
    }
]
```

</details>

To serialise this collection, run:

```bash
stac_generator serialise combined_config.json --id combined --dst generated
```

### Using multiple configs

We can pass multiple config files to the CLI. For instance, to describe all simple configs similar to the previous example, we can run:

```bash
stac_generator serialise point_simple_config.json raster_simple_config.json vector_simple_config.json --id combined --dst generated
```

## Help

To view the supported parameters and keywords for the `serialise` command, run

```
stac_generator serialise --help
```

To view all supported commands, run

```
stac_generator --help
```

Note that  `STAC common metadata` fields can be ignored for now.

## A note on `location` field

Throughout this tutorial, we use relative paths for our asset's location. In practice, we recommend using an absolute path to local asset (if you want to the data to be discovered only locally) or a URL to the hosted asset (if you want to share the metadata and asset with someone else).
