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

from __future__ import annotations

import logging
from argparse import ArgumentParser, Namespace, _SubParsersAction

from pydantic import ValidationError
from rich_argparse import RawDescriptionRichHelpFormatter

from stac_generator.__version__ import __version__

root_logger = logging.getLogger("stac_generator")
logger = logging.getLogger(__name__)


def log_exception(e: Exception, show_stack_trace: bool = False) -> None:
    logger.exception(e, exc_info=show_stack_trace)
    if not show_stack_trace:
        logger.info("Run the command with -v to show detailed error.")


def serialise_handler(args: Namespace) -> None:
    from stac_generator.cli.serialise import serialise_handler as _serialise_handler

    show_stack_trace = False
    if args.v:
        root_logger.setLevel(logging.DEBUG)
        show_stack_trace = True

    # CLI args take precedence over metadata fields
    try:
        _serialise_handler(
            id=args.id,
            src=args.src,
            dst=args.dst,
            title=args.title,
            description=args.description,
            license=args.license,
            num_workers=args.num_workers,
        )
    except ValidationError as e:
        logger.info(
            "Error encountered while parsing config. Fix the error by addressing the following:"
        )
        log_exception(e, show_stack_trace)
    except Exception as e:  # noqa: BLE001
        log_exception(e, show_stack_trace)


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
        default="generated",
        help="""path to where the generated collection is stored.
                Accepts a local path or a remote api endpoint.
                If path is local, collection and item json files will be written to disk.
                If path is an endpoint, the collection and item json files will be pushed using STAC api methods.
                If not value is provided, the folder generated will be created in the current path to store generated records
            """,
    )

    parser.add_argument("-v", action="store_true", help="increase verbosity for debugging")
    # Collection Information
    collection_metadata = parser.add_argument_group("STAC collection metadata")
    collection_metadata.add_argument(
        "--id", type=str, help="id of collection", default="Collection"
    )
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
    collection_metadata.add_argument(
        "--license", type=str, help="STAC license", required=False, default="proprietary"
    )

    # Serialiser metadata
    serialiser_metadata = parser.add_argument_group("Serialliser metadata")
    serialiser_metadata.add_argument(
        "--num_workers",
        type=int,
        required=False,
        default=1,
        help="Number of threads to use for serialisation. If 1, serialisation will be done in a single thread.",
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
    sub_parser = parser.add_subparsers(dest="command", help="Sub commands")
    add_serialise_sub_command(sub_parser)
    args = parser.parse_args()

    if args.command == "serialise":
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    run_cli()
