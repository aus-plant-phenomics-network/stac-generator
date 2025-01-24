## BOM raw data (Time Series measurements)

| longitude | latitude | elevation | station | YYYY-MM-DD | daily_rain | max_temp |
|-----------|----------|-----------|---------|------------|------------|----------|
| 138.519   | -34.952  | 2         | 23304   | 2020-01-01 | 0          | 32.2     |

### BOM Metadata to provide to the STAC Generator 

```
{
  "id": "BOM_Data",
  "location": "path/to/bom.csv",
  "collection_date": "2020-01-01",
  "collection_time": "10:00:00",
  "X": "longitude",
  "Y": "latitude",
  "Z": "elevation", 
  "T": "YYYY-MM-DD",
  "epsg": 4326,
  "column_info": [
    {
      "name": "daily_rain",
      "description": "daily rain fall in mm"
    },
    {
      "name": "max_temp",
      "description": "daily maximum temperature in C"
    }
  ]
}
```

The values for id, location, collection_date, collection_time (required common metadata) are made-up. The values for X, Y, Z, T are obtained from the raw csv - i.e. longitude, latitude, elevation and YYYY-MM-DD respectively. epsg value cannot be derived from the csv and must be known by the user - i.e. reading dataset metadata on BOM/SILO website. The field column_info contains useful columns that the user want to read into the datacube. 

## Soil raw data (No depth, No Timestamp)

| property | field  | profile | easting       | northing  | Ca_Soln |
|----------|--------|---------|---------------|-----------|---------|
| Sunbury  | Jordie | 3       | 773215.36<br> | 678187.36 | 3       |


### Soil Metadata to provide to the STAC Generator 

```
{
  "id": "soil_data",
  "location": "path/to/soil.csv",
  "collection_date": "2020-01-01",
  "collection_time": "10:00:00",
  "X": "easting",
  "Y": "northing",
  "epsg": 28355,
  "column_info": [
    {
      "name": "Ca_Soln",
      "description": "Calcium solution in ppm"
    },
    {
      "name": "profiles",
      "description": "Field profile"
    }
  ]
}

```

The values for id, location, collection_date, collection_time (required common metadata) are made-up. The values for X, Y are obtained from the raw csv - i.e. easting and northing respectively. There is no elevation and time column so they can be left blank. The value for epsg must be known before hand, in this example, we assume it to be GDA94/MGA55 with espg code 28355. Also assuming values for property and field are not important in this example, we don’t include them in column_info. 

## OZBarley Point Data 

OZBarley contains 2 point assets - `OZBarley1_measurement` and `OZBarley2_measurement`. The point asset can be downloaded from the following link: [OZBarley1](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/OZBarley/OZBarley1_measurement.csv), [OZBarley2](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/OZBarley/OZBarley2_measurement.csv). The overall config can be downloaded [here](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/OZBarley/remote_config.json). Note that the `epsg` code is known beforehand. 

## LlaraCampey Point Data

The simplified test case for Llara Campey contains `soil_data.csv` point data. The config can be downloaded [here](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/LlaraCampey/LlaraCampey_config_simplified.json). The asset itself can be downloaded by visiting the `location` reference under `soil_measurement` entry. The link is reproduced [here](https://object-store.rc.nectar.org.au/v1/AUTH_2b454f47f2654ab58698afd4b4d5eba7/mccn-test-data/LlaraCampey/soil_data.csv) for convenience. 
