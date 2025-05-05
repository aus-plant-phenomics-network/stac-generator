For raster assets (`tif`, `geotif`, `tiff`, `geotiff` extensions), in addition to the required [fields](./setup.md#generating-stac-records), users are required to declare recorded bands under `band_info` field. 

## Common bands

In this tutorial, we will describe the asset `L2A_PVI.tif` from the zip folder. The asset is an RGB image with RGB bands.

![](images/quick_start_L2A_PVI_raster_RGB.png)

### Config

We will prepare the following `raster_simple_config.json`:

=== "json"

    ```json title="raster_simple_config.json" linenums="1"
    [
      {
        "id": "L2A_PVI",
        "location": "L2A_PVI.tif",
        "collection_date": "2021-02-21",
        "collection_time": "10:00:17",
        "band_info": [
          {
            "name": "R",
            "common_name": "red",
            "description": "Common name: red, Range: 0.6 to 0.7",
            "wavelength": 0.6645
          },
          {
            "name": "G",
            "common_name": "green",
            "description": "Common name: green, Range: 0.5 to 0.6",
            "wavelength": 0.56
          },
          {
            "name": "B",
            "common_name": "blue",
            "description": "Common name: blue, Range: 0.45 to 0.5",
            "wavelength": 0.4966
          }
        ]
      }
    ]
    ```

=== "yaml"

    ```yaml title="raster_simple_config.yaml" linenums="1"
    - id: L2A_PVI
      location: L2A_PVI.tif
      collection_date: '2021-02-21'
      collection_time: '10:00:17'
      band_info:
      - common_name: red
        description: 'Common name: red, Range: 0.6 to 0.7'
        name: R
        wavelength: 0.6645
      - common_name: green
        description: 'Common name: green, Range: 0.5 to 0.6'
        name: G
        wavelength: 0.56
      - common_name: blue
        description: 'Common name: blue, Range: 0.45 to 0.5'
        name: B
        wavelength: 0.4966
    ```

### Field explanation: 

`band_info` is a list of band objects represented in the raster: 

- `name`: band's name 
- `common_name`: band's name that are more well-known.
- `wavelength`: band's wavelength 
- `description`: band's description 

Aside from `name`, other fields are optional. Note that `common_name` supports a very small subset of well-known [names](https://github.com/stac-extensions/eo/blob/main/README.md#common-band-names). If users provide a `common_name` value that is not on this list, the program will raise an error. 

### Command and Output

Save the config as `raster_simple_config.json` and run the following command: 

```bash
stac_generator serialise raster_simple_config.json 
```

## Uncommon/unknown bands

In this tutorial, we will use the asset `vegetation_cover.tif` asset, which contains a custom band `vegetation_cover`.

![](images/quick_start_vegetation_index_raster_custom.png)

### Config

We will prepare the following `raster_custom_config.json`:

=== "json"

    ```json title="raster_custom_config.json" linenums="1"
    [
      {
        "id": "vegetation_cover",
        "location": "vegetation_cover.tif",
        "collection_date": "2021-02-21",
        "collection_time": "10:00:17",
        "band_info": [
          {
            "name": "vegetation",
            "description": "Vegetation cover level"
          }
        ]
      }
    ]
    ```

=== "yaml"

    ``` yaml title="raster_custom_config.yaml" linenums="1"
    - id: vegetation_cover
      location: vegetation_cover.tif
      collection_date: '2021-02-21'
      collection_time: '10:00:17'
      band_info:
      - description: Vegetation cover level
        name: vegetation  
    ```

Note that we only provide name and description since other information is unknown. 

### Command and Output

To serialise the metadata. Save the config as `raster_custom_config.json` and run the serialisation command:

```bash
stac_generator serialise raster_custom_config.json
```