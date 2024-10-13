from stac_generator.drone_stac_generator import DroneStacGenerator
from stac_generator.sensor_stac_generator import SensorStacGenerator
from stac_generator.generator import StacGenerator
from stac_generator.vector_polygon_stac_generator import VectorPolygonStacGenerator


class StacGeneratorFactory:
    @staticmethod
    def get_stac_generator(data_type, data_file, location_file) -> StacGenerator:
        # Get the correct type of generator depending on the data type.
        if data_type == "drone":
            return DroneStacGenerator(data_file, location_file)
        elif data_type == "sensor":
            return SensorStacGenerator(data_file, location_file)
        elif data_type == "vector":
            return VectorPolygonStacGenerator(data_file, location_file)
        else:
            raise Exception(f"{data_type} is not a valid data type.")
