## Geometry Vectors

In this section, we will describe the shape file `Werribee.geojson`, included in the downloaded zip file. 

If you have QGIS installed, you can open the file in QGIS to visualize the data:

![](images/quick_start_Werribee.png)

#### Config

To describe the shape file, create a configuration file named `vector_simple_config` in one of the supported formats: JSON or YAML.

=== "json"

    ``` json title="vector_simple_config.json"
    [
        {
            "id": "Werribee",
            "location": "Werribee.geojson",
            "collection_date": "2025-01-01",
            "collection_time": "00:00:00"
        }
    ]
    ```

=== "yaml"

    ``` yaml title="vector_simple_config.yaml"
    - id: "Werribee"
      location: "Werribee.geojson"
      collection_date: "2025-01-01"
      collection_time: "00:00:00"
    ```


#### Explanation of Fields

- `id`: The unique identifier for the item. Here, it is Werribee.
- `location`: The relative path to the asset file (Werribee.geojson) in the Example directory.
- `collection_date`: The date the asset was collected.
- `collection_time`: The time the asset was collected.

Save the file in the current directory as vector_simple_config.json or vector_simple_config.yaml.

#### Commands and Output

Now run the stac generator serialise command from the terminal:

```bash
stac_generator serialise vector_simple_config.json
```

After running the command, a new folder named generated will appear in the current directory. Inside the generated folder, you will find:

- collection.json: Contains the STAC Collection metadata.

- Werribee/Werribee.json: Contains the STAC Item metadata for our simple vector.

The `collection.json` and `Werribee.json` files represent the metadata for your asset, compliant with the STAC specification.