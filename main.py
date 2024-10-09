from argparse import ArgumentParser

from stac_generator.base.schema import StacCatalogConfig
from stac_generator.generator_factory import StacGeneratorFactory

if __name__ == "__main__":
    # Build the CLI argument parser
    parser = ArgumentParser()
    # TODO: Best CLI design TBD.
    parser.add_argument("--")
    parser.add_argument("--source_cfg", type=str, help="Path to the config")
    parser.add_argument("--id", type=str, help="Id of collection or catalog")
    parser.add_argument("--title", type=str, help="Id of collection or catalog")
    parser.add_argument("--description", type=str, help="Id of collection or catalog")
    parser.add_argument("--href", type=str, help="Id of collection or catalog")
    parser.add_argument("--endpoint", type=str, help="Id of collection or catalog")
    # Get the filepaths
    args = parser.parse_args()
    # Create the Stac catalog
    config = StacCatalogConfig(
        id=args.id,
        title=args.title,
        description=args.description,
        href=args.href,
        endpoint=args.endpoint,
    )
    generator = StacGeneratorFactory().get_stac_generator(args.source_cfg, config)
    # print(generator.collection.to_dict())
    generator.write_to_api()
