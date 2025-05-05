In the [previous](./vector_geometry.md) tutorial, we created a bare minimum config to describe a vector asset. The generated STAC thus contains only the geometry information. In this example, we will enhance the metadata by adding more descriptive fields such as `title` and `description`. Additionally, we will describe attributes contained within the vector file. We still use the same asset `Werribee.json` in the downloaded zip file. 

For instance, the shape file `Werribee.geojson` has an attribute called `Suburb_Name`:

![](images/quick_start_Werribee_Attribute.png)

---

#### Config

=== "json"

    ```json title="vector_detailed_config.json" linenums="1" hl_lines="7-14"
    [
      {
        "id": "Werribee",
        "location": "Werribee.geojson",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "title": "Werribee Item",
        "description": "Suburbs near Werribee Melbourne",
        "column_info": [
          {
            "name": "Suburb_Name",
            "description": "suburb name"
          }
        ]
      }
    ]
    ```
=== "yaml"

    ```yaml title="vector_detailed_config.yaml" linenums="1" hl_lines="5-9"
    - id: "Werribee"
      location: "Werribee.geojson"
      collection_date: "2025-01-01"
      collection_time: "00:00:00"
      title: "Werribee Item"
      description: "Suburbs near Werribee Melbourne"
      column_info:
        - name: "Suburb_Name"
          description: "suburb name"
    ```

#### Field Explanation

The basic fields are the same as those in the [previous](./vector_geometry.md) section. The additional fields are: 

- `title`: item's title
- `description`: item's description
- `column_info`: contains a list of column objects with attribute `name` and `description`. This field is used
to represent the attributes contained in the vector file.

STAC Common-metadata like `title` and `description` can be included in generated STAC records by adding them in the item config. Users can describe the attributes associated with the vector file through the keyword `column_info`. Users don't need to describe all attributes, but if one of the column objects provided in `column_info` is not present, the program will raise an error. 

To see a list of supported metadata, please refer to the relevant [documentation]().

### Command and Output

Save this config as `vector_detailed_config.json`/`vector_detailed_config.yaml` in the same folder and run the serialisation command:

```bash
stac_generator serialise vector_detailed_config.json
```

The fields `title`, `description`, and `column_info` should appear correctly under the generated item's `properties`.