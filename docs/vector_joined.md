In many spatial applications, geometry information is stored separately from attributes, typically in different tables. A join operation is performed at runtime to combine the two datasets. To simplify this workflow, we assume:

- Geometry information is extracted and stored in a vector file.
- Attributes are extracted and stored in a CSV file.

The STAC generator can describe this join operation by including a few additional keywords in the configuration.

## Generic Join Asset

For this example, we assume the vector file `Werribee.geojson` has an accompanied attribute table stored in the file `distance.csv`.

{{ read_csv('tests/files/unit_tests/vectors/distance.csv') }}

The asset contains some attributes associated with different suburbs near Werribee. The values of `Area` in the join asset have a 1-to-1 correspondence with the values of the attribute `Suburb_Name` in the vector [asset](./vector_attributes.md).

### Config

=== "json"

    ```json title="vector_join_config.json" linenums="1" hl_lines="13-43"
    [
      {
        "id": "Werribee",
        "location": "Werribee.geojson",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "column_info": [
          {
            "name": "Suburb_Name",
            "description": "Suburb_Name"
          }
        ],
        "join_config": {
          "file": "distance.csv",
          "left_on": "Suburb_Name",
          "right_on": "Area",
          "column_info": [
            {
              "name": "Area",
              "description": "Area name"
            },
            {
              "name": "Distance",
              "description": "Driving Distance to CBD in km"
            },
            {
              "name": "Public_Transport",
              "description": "Time taken to reach CBD by public transport in minutes"
            },
            {
              "name": "Drive",
              "description": "Time taken to reach CBD by driving in minutes"
            },
            {
              "name": "Growth",
              "description": "Average 5 year growth in percentage in 2025"
            },
            {
              "name": "Yield",
              "description": "Average rental yield in 2025"
            }
          ]
        }
      }
    ]
    ```

=== "yaml"

    ``` yaml title="vector_join_config.yaml" linenums="1" hl_lines="8-24"
    - id: Werribee
      location: Werribee.geojson
      collection_date: '2025-01-01'
      collection_time: 00:00:00
      column_info:
      - description: Suburb_Name
        name: Suburb_Name
      join_config:
        file: distance.csv
        left_on: Suburb_Name
        right_on: Area
        column_info:
          - description: Area
            name: Area name
          - description: Driving Distance to CBD in km
            name: Distance
          - description: Time taken to reach CBD by public transport in minutes
            name: Public_Transport
          - description: Time taken to reach CBD by driving in minutes
            name: Drive
          - description: Average 5 year growth in percentage in 2025
            name: Growth
          - description: Average rental yield in 2025
            name: Yield
    ```
### Explanation of fields

The first part of the config is similar to that of the [previous](./vector_attributes.md) tutorial, in which we describe the minimum required fields and the vector's attributes. We also specify the following additional fields:

- `join_config`: contains metadata for the join asset
- `file`: path to the join asset
- `left_on`: attribute from the vector that will be used for the join operation.
- `right_on`: attribute from the join asset that will be used for the join operation.
- `column_info`: attributes of the join asset.

The join terminologies that we use are consistent with pandas' [merge](https://pandas.pydata.org/docs/reference/api/pandas.merge.html) operation's, in which the vector geometry is treated as the left dataframe, while the join asset the right dataframe. The join operation is `inner left join`, where rows with matching values of `left_on` and `right_on` are merged. Note that the field `left_on` must be described in the vector's `column_info` while `right_on` described in the join asset's `column_info`. If either of those fields are not described appropriately, an error will be raised.

### Command and Output

Save the config as `vector_join_config.json` and run the following command:

```bash
stac_generator serialise vector_join_config.json
```

You should see the corresponding fields appearing under `properties` in `Werribee.json`.

## Timeseries Join Asset

In this example, we will use the join asset `price.csv` as attributes for the vector file `Werribee.geojson`. The asset file is presented as follows:

{{ read_csv('tests/files/unit_tests/vectors/price.csv') }}

The asset contains the sale and rental prices of various surburbs in Werribee over three different time periods 2020, 2024 and 2025. Similarly, the attribute `Area` of the join asset is used to perform the join operation with the attribute  `Suburb_Name` of the vector asset.

### Config

=== "json"

    ```json title="vector_join_date_config.json" linenums="1" hl_lines="17"
    [
      {
        "id": "Werribee",
        "location": "Werribee.geojson",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "column_info": [
          {
            "name": "Suburb_Name",
            "description": "Suburb_Name"
          }
        ],
        "join_config": {
          "file": "price.csv",
          "left_on": "Suburb_Name",
          "right_on": "Area",
          "date_column": "Date",
          "column_info": [
            {
              "name": "Area",
              "description": "Area Name"
            },
            {
              "name": "Sell_Price",
              "description": "Median Sales Price in 2025"
            },
            {
              "name": "Rent_Price",
              "description": "Median Rental Price in 2025"
            },
            {
              "name": "Sell/Rent",
              "description": "Ratio of Sales Price (in $1000) over Rental Price (in $)"
            }
          ]
        }
      }
    ]
    ```

=== "yaml"

    ``` yaml title="vector_join_date_config.yaml" linenums="1" hl_lines="12"
    - id: Werribee
      collection_date: '2025-01-01'
      collection_time: 00:00:00
      location: Werribee.geojson
      column_info:
      - description: Suburb_Name
        name: Suburb_Name
      join_config:
        file: price.csv
        left_on: Suburb_Name
        right_on: Area
        date_column: Date
        column_info:
        - description: Area Name
          name: Area
        - description: Median Sales Price in 2025
          name: Sell_Price
        - description: Median Rental Price in 2025
          name: Rent_Price
        - description: Ratio of Sales Price (in $1000) over Rental Price (in $)
          name: Sell/Rent
    ```

### Field Explanation

The config uses the same set of fields as the config for generic join asset. The additional keyword is:

- `date_column`: describes the attribute in the csv to be used as timestamps. From `price.csv`, this columns is `Date`.

By default, date values in `date_column` will be parsed using ISO8601 date format. If date values are encoded with a custom format, the format can be provided using the field `date_format`. The date formats follows python's strptime [formats](https://docs.python.org/3/library/datetime.html#strftime-and-strptime-format-codes). Note that if the date column cannot be found in the asset or date values cannot be parsed (either using ISO8601 or `date_format` value if provided), the program will raise an error.

### Command and Output

Save the config as `vector_join_date_config.json` and run the following command:

``` bash
stac_generator serialise vector_join_date_config.json
```

The output should contain the specified fields.
