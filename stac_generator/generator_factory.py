from stac_generator.drone_stac_generator import DroneStacGenerator
from stac_generator.generator import StacGenerator
from stac_generator.sensor_stac_generator import SensorStacGenerator

__all__ = ("StacGeneratorFactory",)


class StacGeneratorFactory:
    @staticmethod
    def get_stac_generator(data_type, data_file, location_file) -> StacGenerator:  # type: ignore[no-untyped-def]
        # Get the correct type of generator depending on the data type.
        if data_type == "drone":
            return DroneStacGenerator(data_file, location_file)
        if data_type == "sensor":
            return SensorStacGenerator(data_file, location_file)
        raise Exception(f"{data_type} is not a valid data type.")
