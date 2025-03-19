r"""
  /$$$$$$ /$$$$$$$$/$$$$$$  /$$$$$$         /$$$$$$ /$$$$$$$$/$$   /$$
 /$$__  $|__  $$__/$$__  $$/$$__  $$       /$$__  $| $$_____| $$$ | $$
| $$  \__/  | $$ | $$  \ $| $$  \__/      | $$  \__| $$     | $$$$| $$
|  $$$$$$   | $$ | $$$$$$$| $$            | $$ /$$$| $$$$$  | $$ $$ $$
 \____  $$  | $$ | $$__  $| $$            | $$|_  $| $$__/  | $$  $$$$
 /$$  \ $$  | $$ | $$  | $| $$    $$      | $$  \ $| $$     | $$\  $$$
|  $$$$$$/  | $$ | $$  | $|  $$$$$$/      |  $$$$$$| $$$$$$$| $$ \  $$
 \______/   |__/ |__/  |__/\______/        \______/|________|__/  \__/
"""  # noqa: D212

import json
import logging
from argparse import ArgumentParser, Namespace, _SubParsersAction
from pathlib import Path

from rich_argparse import RawDescriptionRichHelpFormatter

from stac_generator.__version__ import __version__
from stac_generator.core.base.generator import StacSerialiser
from stac_generator.core.base.schema import StacCollectionConfig
from stac_generator.factory import StacGeneratorFactory

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def template_handler(args: Namespace) -> None:
    pass


def serialise_handler(args: Namespace) -> None:
    if args.v:
        import logging

        logging.getLogger().setLevel(logging.DEBUG)
    # Build collection config and catalog config
    metadata_json = {}
    if args.metadata_json:
        with Path(args.metadata_json).open("r") as file:
            metadata_json = json.load(file)

    # CLI args take precedence over metadata fields
    collection_config = StacCollectionConfig(
        id=args.id,
        title=args.title,
        description=args.description,
        license=args.license if args.license else metadata_json.get("license"),
        platform=args.platform if args.platform else metadata_json.get("platform"),
        constellation=args.constellation
        if args.constellation
        else metadata_json.get("constellation"),
        mission=args.mission if args.mission else metadata_json.get("mission"),
        instruments=args.instruments if args.instruments else metadata_json.get("instruments"),
        providers=metadata_json.get("providers"),
    )

    # Generate
    generator = StacGeneratorFactory.get_stac_generator(
        source_configs=args.src,
        collection_config=collection_config,
    )
    # Save
    serialiser = StacSerialiser(generator, args.dst)
    serialiser()


def add_template_sub_command(sub_parser: _SubParsersAction) -> None:
    template_parser = sub_parser.add_parser(
        "template", help="Generate config template with prefilled information"
    )
    template_parser.add_argument(
        "src",
        type=str,
        action="extend",
        nargs="+",
        help="""path to the source_config.
                Path can be a local path or a url.
                Path also accepts multiple values.
                Source config contains metadata specifying how a raw file is read.
                At the minimum, it must contain the file location.
                To learn more about source config, please visit INSERT_DOC_URL.
            """,
    )
    template_parser.add_argument(
        "--dst", type=str, help="path to dst conflig template. Only csv and json are supported"
    )
    template_parser.set_defaults(func=template_handler)


def add_serialise_sub_command(sub_parser: _SubParsersAction) -> None:
    parser = sub_parser.add_parser("serialise", help="Generate STAC record")
    # Source commands
    parser.add_argument(
        "src",
        type=str,
        action="extend",
        nargs="+",
        help="""path to the source_config.
                Path can be a local path or a url.
                Path also accepts multiple values.
                Source config contains metadata specifying how a raw file is read.
                At the minimum, it must contain the file location.
                To learn more about source config, please visit INSERT_DOC_URL.
            """,
    )
    parser.add_argument(
        "--dst",
        type=str,
        required=True,
        help="""path to where the generated collection is stored.
                Accepts a local path or a remote api endpoint.
                If path is local, collection and item json files will be written to disk.
                If path is an endpoint, the collection and item json files will be pushed using STAC api methods
            """,
    )

    parser.add_argument("-v", action="store_true", help="increase verbosity for debugging")
    # Collection Information
    collection_metadata = parser.add_argument_group("STAC collection metadata")
    collection_metadata.add_argument("--id", type=str, help="id of collection")
    collection_metadata.add_argument(
        "--title", type=str, help="title of collection", required=False, default="Auto-generated."
    )
    collection_metadata.add_argument(
        "--description",
        type=str,
        help="description of collection",
        required=False,
        default="Auto-generated",
    )

    # STAC Common Metadata
    common_metadata = parser.add_argument_group("STAC common metadata")
    common_metadata.add_argument(
        "--license", type=str, help="STAC license", required=False, default="proprietary"
    )
    common_metadata.add_argument(
        "--platform", type=str, help="STAC platform", required=False, default=None
    )
    common_metadata.add_argument(
        "--constellation", type=str, help="STAC constellation", required=False, default=None
    )
    common_metadata.add_argument(
        "--mission", type=str, help="STAC mission", required=False, default=None
    )
    common_metadata.add_argument(
        "--instruments",
        action="extend",
        nargs="+",
        type=str,
        required=False,
        default=None,
        help="STAC instrument",
    )
    common_metadata.add_argument(
        "--metadata_json",
        type=str,
        required=False,
        default=None,
        help="path to json file describing the metadata",
    )
    parser.set_defaults(func=serialise_handler)


def run_cli() -> None:
    # Build the CLI argument parser
    parser = ArgumentParser(
        prog="stac_generator",
        description=__doc__,
        formatter_class=RawDescriptionRichHelpFormatter,
    )
    parser.add_argument("-V", "--version", action="version", version=__version__)
    sub_parser = parser.add_subparsers(help="Sub commands")
    add_template_sub_command(sub_parser)
    add_serialise_sub_command(sub_parser)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    run_cli()
