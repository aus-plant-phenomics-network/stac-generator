import datetime
from typing import Any

from stac_generator.core.base.generator import StacSerialiser
from stac_generator.core.base.schema import ColumnInfo, StacCollectionConfig
from stac_generator.core.point.schema import PointConfig
from stac_generator.factory import StacGeneratorFactory

# Defining a config from a json file

vector_config: str = "vector_simple_config.json"

# Defining a config as a dictionary

raster_config: dict[str, Any] = {
    "id": "vegetation_cover",
    "location": "vegetation_cover.tif",
    "collection_date": "2021-02-21",
    "collection_time": "10:00:17",
    "band_info": [{"name": "vegetation", "description": "Vegetation cover level"}],
}

# Defining a config as a Config object
point_config = PointConfig(
    id="soil_data",
    location="soil_data.csv",
    collection_date=datetime.date(2020, 1, 1),
    collection_time=datetime.time(10),
    X="Longitude",
    Y="Latitude",
    epsg=4326,
    column_info=[ColumnInfo(name="Cal_Soln", description="Calcium Soln in ppm")],
)

# Create a Collection Generator
collection_generator = StacGeneratorFactory.get_collection_generator(
    source_configs=[point_config, vector_config, raster_config],
    collection_config=StacCollectionConfig(id="collection"),
)
# Serialise data
serialiser = StacSerialiser(collection_generator, "generated")
serialiser()
