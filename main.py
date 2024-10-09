from argparse import ArgumentParser

from stac_generator.base.schema import StacCollectionConfig
from stac_generator.generator_factory import StacGeneratorFactory

if __name__ == "__main__":
    # Build the CLI argument parser
    parser = ArgumentParser()
    # TODO: Best CLI design TBD.
    parser.add_argument("source", "--source", type=str, help="path to the config csv")
    parser.add_argument("--dtype", type=str, help="data type of the source data")
    parser.add_argument("--id", type=str, help="id of collection or catalog")
    parser.add_argument("--title", type=str, help="title of collection or catalog")
    parser.add_argument("--description", type=str, help="description of collection or catalog")
    parser.add_argument(
        "--href",
        type=str,
        help="href of catalog, for saving to disk or as endpoint for POST request",
    )

    # Get the filepaths
    args = parser.parse_args()
    # Create the Stac catalog
    collection_cfg = StacCollectionConfig(
        title=args.title,
        description=args.description,
        id=args.id,
    )
    generator = StacGeneratorFactory.get_stac_generator(
        data_type=args.dtype,
        source_file=args.source,
        collection_cfg=collection_cfg,
        href=args.href,
    )
