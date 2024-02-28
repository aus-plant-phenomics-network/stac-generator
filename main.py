from argparse import ArgumentParser
from pathlib import Path

from stac_generator.generator import (
    DroneStacGenerator,
    SensorStacGenerator,
    StacGenerator,
)


class StacGeneratorFactory:
    @staticmethod
    def get_drone_stac_generator(data_type, data_file) -> StacGenerator:
        if data_type == "drone":
            return DroneStacGenerator(data_file)
        elif data_type == "sensor":
            return SensorStacGenerator(data_file)
        else:
            raise Exception(f"{data_type} is not a valid data type")


if __name__ == "__main__":
    parser = ArgumentParser()
    # TODO: Best CLI  design TBD.
    parser.add_argument(
        "-f", "--file", type=str, help="Path to the dataset's metadata standard"
    )
    args = parser.parse_args()
    data_file = Path(args.file)
    data_type = data_file.stem.split("_")[0]
    generator = StacGeneratorFactory().get_drone_stac_generator(data_type, data_file)
    generator.validate_data()
    generator.generate()
