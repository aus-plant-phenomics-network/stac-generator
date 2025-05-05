It is not uncommon to have a multiple shape files compressed into a single zip for archival. The STAC Generator provides some mechanism for handling zipped vector files without having to uncompress the file. In this tutorial, we will make use of `SA2.zip`, which contains the shape files for the Werribee and Sunbury suburbs in Victoria.

![](images/quick_start_SA2.png)

Here we have two layers - Sunbury and Werribee, and each layer will be generated as a STAC item with indepdent config entries. If there are multiple layers in a zip file, users can choose which layer to describe.

### Config

=== "json"

    ```json title="vector_layer_config.json" linenums="1" hl_lines="7 14"
    [
      {
        "id": "WerribeeSA2",
        "location": "SA2.zip",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "layer": "Werribee"
      },
      {
        "id": "SunburySA2",
        "location": "SA2.zip",
        "collection_date": "2025-01-01",
        "collection_time": "00:00:00",
        "layer": "Sunbury"
      }
    ]
    ```

=== "yaml"

    ```yaml title="vector_layer_config.yaml" linenums="1" hl_lines="4 8"
    - id: WerribeeSA2
      collection_date: '2025-01-01'
      collection_time: 00:00:00
      layer: Werribee
      location: SA2.zip
    - id: SunburySA2
      collection_date: '2025-01-01'
      collection_time: 00:00:00
      layer: Sunbury
      location: SA2.zip
    ```

### Field Explanations

- `layer`: the layer name in the zip file.

Note that if layer name is not present in the zip file, the program will raise an error. 

### Command and Output 

Save the new config as `vector_layer_config.json` and run the command:

```
stac_generator serialise vector_layer_config.json
```

You will see two items generated, `WerribeSA2` and `SunburySA2`. Note that each config record has a `layer` keyword to identify the layer in the compressed zip. We use a simple config to describe each layer, but it is possible to add additional information like column info and join attributes as described in the previous sections.