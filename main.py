from argparse import ArgumentParser
from pathlib import Path

from stac_generator.generator import StacGeneratorFactory

if __name__ == "__main__":
    # Build the CLI argument parser
    parser = ArgumentParser()
    # TODO: Best CLI design TBD.
    parser.add_argument(
        "-f", "--file", type=str, help="Path to the dataset's metadata schema."
    )
    # Get the filepath
    args = parser.parse_args()
    data_file = Path(args.file)
    data_type = data_file.stem.split("_")[0]
    # Create the STAC catalog
    generator = StacGeneratorFactory().get_stac_generator(data_type, data_file)
    generator.validate_data()
    generator.generate()
    generator.validate_stac()
