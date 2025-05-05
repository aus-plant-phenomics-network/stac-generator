The `stac_generator` uses the `csv` and `txt` extensions to describe point data. In addition to the minimum required [fields](./setup.md#generating-stac-records), the STAC generator requires a few additional parameters to properly parse the asset. 

Given the flexibility of the csv format, we require point dataset to be structured in a particular way. Each row of the csv file describes a point, with columns being the attributes. At the minimum, there must be two columns describing the coordinates of the points, with the common options being `lat/lon`, `y/x`, `northings/eastings`, etc. The required config fields include:

- `X`: the column in the csv asset to describe the longitude.
- `Y`: the column in the csv asset to describe the latitude.
- `epsg`: the crs of the `X`, `Y` columns.

There can also be optional columns:

- `T`: the column in the csv asset that describes the date of collection of a point record.
- `date_format`: how the date string is interpreted - by default, dates are assumed to be `ISO8640` compliant.
- `Z`: the column in the csv asset that describes the altitude.
-  `column_info`: describe the relevant names and descriptions of relavant attributes.

## Generic Point Data

In this tutorial, we will describe the asset `soil_data.csv` contained in the zip folder.

{{ read_csv("tests/files/integration_tests/point/data/soil_data.csv") }}

### Config 

The config - `point_simple_config.json` is described below:

=== "json"

    ```json title="point_simple_config.json" linenums="1" hl_lines="7-15"
    [
      {
        "id": "soil_data",
        "location": "soil.csv",
        "collection_date": "2020-01-01",
        "collection_time": "10:00:00",
        "X": "Longitude",
        "Y": "Latitude",
        "epsg": 4326,
        "column_info": [
          {
            "name": "Ca_Soln",
            "description": "Calcium solution in ppm"
          },
        ]
      }
    ]
    ```

=== "yaml"

    ```yaml title="point_simple_config.yaml" linenums="1" hl_lines="3-10"
    - id: soil_data
      location: soil_data.csv
      epsg: 4326
      X: Longitude
      Y: Latitude
      collection_date: '2020-01-01'
      collection_time: '10:00:00'
      column_info:
      - description: Calcium solution in ppm
        name: Ca_Soln
    ```

### Field Explanations

- `X`: the x coordinate of the data is `Longitude`.
- `Y`: the y coordinate of the data is `Latitude`.
- `epsg`: we assume the data is recorded in WGS84 or epsg 4326.
- `column_info`: similar to the same field in [vector](./vector_attributes.md) assets. This is a list of column objects with fields `name` and `description`. In this example, we describe the attribute `ca_soln`.

### Command and Output 

Save the config file as `point_simple_config.json` and run the follow serialisation command: 

```bash
stac_generator serialise point_simple_config.json
```

## Timeseries Point Data

In this tutorial, we describe the asset `adelaide_airport.csv` which contains weather station collected by a BOM station in the area: 

{{ read_csv("tests/files/integration_tests/point/data/adelaide_airport.csv") }}


### Config

We prepare the `point_time_series_config.json` as follows:

=== "json"

    ```json title="point_time_series_config.json" linenums="1" hl_lines="10"
    [
      {
        "id": "adelaide_airport",
        "location": "tests/files/integration_tests/point/data/adelaide_airport.csv",
        "collection_date": "2023-01-01",
        "collection_time": "09:00:00",
        "X": "longitude",
        "Y": "latitude",
        "Z": "elevation",
        "T": "YYYY-MM-DD",
        "epsg": 7843,
        "column_info": [
          {
            "name": "daily_rain",
            "description": "Observed daily rain fall in mm"
          },
          {
            "name": "max_temp",
            "description": "Observed daily maximum temperature in degree C"
          },
          {
            "name": "min_temp",
            "description": "Observed daily minimum temperature in degree C"
          },
          {
            "name": "radiation",
            "description": "Total incoming downward shortwave radiation on a horizontal surface MJ/sqm"
          },
          {
            "name": "mslp",
            "description": "Mean sea level pressure in hPa"
          }
        ]
      }
    ]
    ```
=== "yaml"

    ```yaml title="point_time_series_config.yaml" linenums="1" hl_lines="8"
    - id: adelaide_airport
      location: adelaide_airport.csv
      collection_date: '2023-01-01'
      collection_time: 09:00:00
      X: longitude
      Y: latitude
      Z: elevation
      T: YYYY-MM-DD
      epsg: 7843
      column_info:
      - description: Observed daily rain fall in mm
        name: daily_rain
      - description: Observed daily maximum temperature in degree C
        name: max_temp
      - description: Observed daily minimum temperature in degree C
        name: min_temp
      - description: Total incoming downward shortwave radiation on a horizontal surface
          MJ/sqm
        name: radiation
      - description: Mean sea level pressure in hPa
        name: mslp
    ```

</details>

### Field Explanation

- `T`: describe the name of the time column - i.e. `YYYY-MM-DD`.

In summary, the values for `X`, `Y`, `Z`, `T` are obtained from the raw csv - i.e. longitude, latitude, elevation and YYYY-MM-DD respectively.

`epsg` value cannot be derived from the csv and must be known by the user - i.e. reading dataset metadata on BOM/SILO website.

### Command and Output

Save the config as `point_time_series_config.json`. Run the following command to serialise the metadata:

```bash
stac_generator serialise point_time_series_config.json
```