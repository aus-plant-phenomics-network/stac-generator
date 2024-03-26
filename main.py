from argparse import ArgumentParser
from pathlib import Path

from stac_generator.generator_factory import StacGeneratorFactory

if __name__ == "__main__":
    # Build the CLI argument parser
    parser = ArgumentParser()
    # TODO: Best CLI design TBD.
    parser.add_argument("metadata", type=str, help="Path to the dataset's metadata schema.")
    parser.add_argument(
        "-f", "--file", type=str, help="Path to the file containing a list of data locations."
    )
    # Get the filepaths
    args = parser.parse_args()
    data_file = Path(args.metadata)
    data_type = data_file.stem.split("_")[0]
    location_file = Path(args.file)
    # Create the STAC catalog
    generator = StacGeneratorFactory().get_stac_generator(data_type, data_file, location_file)
    # print(generator.collection.to_dict())
    generator.write_to_api()
