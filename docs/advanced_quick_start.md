## Using `stac_generator` as a python module

In the previous [tutorial](./quick_start.md), we have seen how `stac_generator` can be used as a command line tool to generate STAC metadata. In this section, we will demonstrate how to write a Python script that imports the `stac_generator` modules and perform tasks in the [previous](./quick_start.md/#using-a-combined-config) section:

<details>

<summary>PYTHON</summary>

``` { .py linenums="1" title="generate_collection.py" }
import datetime

from stac_generator.core.base import (
    StacCollectionConfig,
    StacSerialiser,
)
from stac_generator.core.raster import RasterConfig
from stac_generator.factory import StacGeneratorFactory

# CSV Config - Instantiate the config using a dictionary
point_config = {
    "id": "soil_data",
    "location": "soil.csv",
    "collection_date": "2020-01-01",
    "collection_time": "10:00:00",
    "X": "eastings_utm",
    "Y": "northings_utm",
    "epsg": 28355,
    "column_info": [
        {"name": "ca_soln", "description": "Calcium solution in ppm"},
        {"name": "profile", "description": "Field profile"},
    ],
}


# Raster Config - Instantiate using a known config class
raster_config = RasterConfig(
    id="l2a_pvi",
    location="L2A_PVI.tif",
    collection_date=datetime.date(year=2020, month=1, day=1),
    collection_time=datetime.time(hour=0, minute=0, second=0),
    band_info=[
        {
            "name": "B04",
            "common_name": "red",
            "description": "Common name: red, Range: 0.6 to 0.7",
            "wavelength": 0.6645,
        },
        {
            "name": "B03",
            "common_name": "green",
            "description": "Common name: green, Range: 0.5 to 0.6",
            "wavelength": 0.56,
        },
        {
            "name": "B02",
            "common_name": "blue",
            "description": "Common name: blue, Range: 0.45 to 0.5",
            "wavelength": 0.4966,
        },
    ],
)

# Vector Config - Instantiate using a file - provides a file path
vector_config = "vector_detailed_config.json"

# Collection Config
collection_config = StacCollectionConfig(
    id="collection",
    title="tutorial collection",
    description="collection generated using apis instead of CLI",
    license="MIT",
)

# Create generator
generator = StacGeneratorFactory.get_collection_generator(
    source_configs=[raster_config, vector_config, point_config],
    collection_config=collection_config,
)
# Serialise collection
serialiser = StacSerialiser(generator, "generated")
serialiser()
```

</details>

The steps include:

- Declaring item configs
- Declaring collection config
- Creating a generator object by passing the item configs and collection configs to `StacGeneratorFactor.get_collection_generator`.
- Creating the serialiser object with `StacSerialiser` and call the object.

## Declaring item configs

The first step is to prepare the config. In general, there are three ways to declare a config:

- Using a config file.
- Using a regular python dictionary.
- Using a known config class.

To declare the config from a file, you will need to provide the path to the config file that can be accessed in the current path. For instance, in the previous example, we use [vector_detailed_config.json](./quick_start.md/#describing-vector-attributes) as the vector config.

To declare the config using a dictionary, you will need to write a python dictionary with the necessary fields declared. Note how the python dictionary in the previous example has the exact same content as the config in the [previous](./quick_start.md/#describing-generic-point-data) tutorial.

Using a known config class in the recommended approach. If you already know the data type of the asset, you can use one of `VectorConfig`, `RasterConfig`, `PointConfig` to declare the config. If you have a linter available, the linter can help pre-validate your input or suggest missing required fields when using the config classes.

## Saving configs to file

This section describes how you can save the configs declared programmatically to a json file. We provide two convenient methods for serialising configs:

- If you want to generate a composite config for the entire collection, use `StacSerialiser`'s `save_collection_config` method.
- If you want to save individual config to a file, use `StacSerialiser`'s `save_configs` static method.

For instance, if we want to create a composite config for the previous example:

``` { .py linenums="1"}
# Declare item and collection configs
# Create generator
generator = StacGeneratorFactory.get_collection_generator(
    source_configs=[raster_config, vector_config, point_config],
    collection_config=collection_config,
)
# Serialise collection
serialiser = StacSerialiser(generator, "generated")
# serialiser()
serialiser.save_collection_config("composite_config.json")
```

The full script is provided as follows:

<details>
<summary>PYTHON</summary>

``` { .py linenums="1" hl_lines="72"}
import datetime

from stac_generator.core.base import (
    StacCollectionConfig,
    StacSerialiser,
)
from stac_generator.core.raster import RasterConfig
from stac_generator.factory import StacGeneratorFactory

# CSV Config - Instantiate the config using a dictionary
point_config = {
    "id": "soil_data",
    "location": "soil.csv",
    "collection_date": "2020-01-01",
    "collection_time": "10:00:00",
    "X": "eastings_utm",
    "Y": "northings_utm",
    "epsg": 28355,
    "column_info": [
        {"name": "ca_soln", "description": "Calcium solution in ppm"},
        {"name": "profile", "description": "Field profile"},
    ],
}


# Raster Config - Instantiate using a known config class
raster_config = RasterConfig(
    id="l2a_pvi",
    location="L2A_PVI.tif",
    collection_date=datetime.date(year=2020, month=1, day=1),
    collection_time=datetime.time(hour=0, minute=0, second=0),
    band_info=[
        {
            "name": "B04",
            "common_name": "red",
            "description": "Common name: red, Range: 0.6 to 0.7",
            "wavelength": 0.6645,
        },
        {
            "name": "B03",
            "common_name": "green",
            "description": "Common name: green, Range: 0.5 to 0.6",
            "wavelength": 0.56,
        },
        {
            "name": "B02",
            "common_name": "blue",
            "description": "Common name: blue, Range: 0.45 to 0.5",
            "wavelength": 0.4966,
        },
    ],
)

# Vector Config - Instantiate using a file - provides a file path
vector_config = "vector_detailed_config.json"

# Collection Config
collection_config = StacCollectionConfig(
    id="collection",
    title="tutorial collection",
    description="collection generated using apis instead of CLI",
    license="MIT",
)

# Create generator
generator = StacGeneratorFactory.get_collection_generator(
    source_configs=[raster_config, vector_config, point_config],
    collection_config=collection_config,
)
# Serialise collection
serialiser = StacSerialiser(generator, "generated")
serialiser.save_collection_config("composite_config.json")
```

</details>



Alternatively, if we want to save raster and point configs to `raster_point_config.json`, we can do the following:

``` { .py}
# Declare item configs

# serialiser()
StacSerialiser.save_config([raster_config, point_config],"raster_point_config.json")
```

The full script is provided as follows:

<details>
<summary>PYTHON</summary>

``` { .py linenums="1" hl_lines="58"}
import datetime

from stac_generator.core.base import (
    StacCollectionConfig,
    StacSerialiser,
)
from stac_generator.core.raster import RasterConfig
from stac_generator.factory import StacGeneratorFactory

# CSV Config - Instantiate the config using a dictionary
point_config = {
    "id": "soil_data",
    "location": "soil.csv",
    "collection_date": "2020-01-01",
    "collection_time": "10:00:00",
    "X": "eastings_utm",
    "Y": "northings_utm",
    "epsg": 28355,
    "column_info": [
        {"name": "ca_soln", "description": "Calcium solution in ppm"},
        {"name": "profile", "description": "Field profile"},
    ],
}


# Raster Config - Instantiate using a known config class
raster_config = RasterConfig(
    id="l2a_pvi",
    location="L2A_PVI.tif",
    collection_date=datetime.date(year=2020, month=1, day=1),
    collection_time=datetime.time(hour=0, minute=0, second=0),
    band_info=[
        {
            "name": "B04",
            "common_name": "red",
            "description": "Common name: red, Range: 0.6 to 0.7",
            "wavelength": 0.6645,
        },
        {
            "name": "B03",
            "common_name": "green",
            "description": "Common name: green, Range: 0.5 to 0.6",
            "wavelength": 0.56,
        },
        {
            "name": "B02",
            "common_name": "blue",
            "description": "Common name: blue, Range: 0.45 to 0.5",
            "wavelength": 0.4966,
        },
    ],
)

# Vector Config - Instantiate using a file - provides a file path
vector_config = "vector_detailed_config.json"

# Serialise individual configs
StacSerialiser.save_config([raster_config, point_config],"raster_point_config.json")
```

</details>
