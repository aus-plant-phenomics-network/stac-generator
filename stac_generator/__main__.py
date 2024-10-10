import asyncio
import datetime
import json
import sys
from argparse import ArgumentParser
from pathlib import Path

from stac_generator.__version__ import __version__
from stac_generator.base.schema import StacCatalogConfig, StacCollectionConfig
from stac_generator.generator_factory import StacGeneratorFactory


def run_cli() -> None:
    # Build the CLI argument parser
    parser = ArgumentParser(prog="stac_generator", description="CLI tool to generator STAC records")
    parser.add_argument("-v", "--version", action="version", version=__version__)
    # Source commands
    parser.add_argument("data_type", type=str, help="data type of the source data")
    parser.add_argument("source_file", type=str, help="path to the source config csv")
    parser.add_argument(
        "--to_remote",
        type=str,
        required=False,
        default=None,
        help="catalog api endpoint for pushing generated stac records",
    )
    parser.add_argument(
        "--to_local",
        type=str,
        required=False,
        default=None,
        help="local path to save generated stac records to",
    )

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

    # Catalog Information
    catalog_metadata = parser.add_argument_group(
        "STAC catalog metadata- Derived from STAC Collection metadata if not provided"
    )
    catalog_metadata.add_argument(
        "--catalog_id",
        type=str,
        required=False,
        help="id of catalog. Use the value of id if not provided",
    )
    catalog_metadata.add_argument(
        "--catalog_title",
        type=str,
        required=False,
        help="title of catalog. Use the value of title if not provided",
    )
    catalog_metadata.add_argument(
        "--catalog_description",
        type=str,
        required=False,
        help="description of catalog. Use the value of description if not provided",
    )

    # STAC Common Metadata
    common_metadata = parser.add_argument_group(
        "STAC common metadata. Providers information can only be provided from a metadata json file. CLI arguments take priority over json fields if overlapping occurs"
    )
    common_metadata.add_argument(
        "--datetime",
        type=datetime.datetime.fromisoformat,
        help="STAC datetime",
        required=False,
        default=None,
    )
    common_metadata.add_argument(
        "--start_datetime",
        type=datetime.datetime.fromisoformat,
        help="STAC start_datetime",
        required=False,
        default=None,
    )
    common_metadata.add_argument(
        "--end_datetime",
        type=datetime.datetime.fromisoformat,
        help="STAC end_datetime",
        required=False,
        default=None,
    )
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
    common_metadata.add_argument("--gsd", type=float, help="STAC gsd", required=False, default=None)
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
    args = parser.parse_args()

    if args.to_remote is None and args.to_local is None:
        sys.exit("Error - either --to_remote or --to_local must be provided")

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
        datetime=args.datetime if args.datetime else metadata_json.get("datetime"),
        start_datetime=args.start_datetime
        if args.start_datetime
        else metadata_json.get("start_datetime"),
        end_datetime=args.end_datetime if args.end_datetime else metadata_json.get("end_datetime"),
        license=args.license if args.license else metadata_json.get("license"),
        platform=args.platform if args.platform else metadata_json.get("platform"),
        constellation=args.constellation
        if args.constellation
        else metadata_json.get("constellation"),
        mission=args.mission if args.mission else metadata_json.get("mission"),
        gsd=args.gsd if args.gsd else metadata_json.get("gsd"),
        instruments=args.instruments if args.instruments else metadata_json.get("instruments"),
        providers=metadata_json.get("providers"),
    )
    # CLI catalog args take precendence over collection args
    catalog_config = StacCatalogConfig(
        id=args.catalog_id if args.catalog_id else args.id,
        title=args.catalog_title if args.catalog_title else args.title,
        description=args.catalog_description if args.catalog_description else args.description,
    )
    # Generate
    generator = StacGeneratorFactory.get_stac_generator(
        data_type=args.data_type,
        source_file=args.source_file,
        collection_cfg=collection_config,
        catalog_cfg=catalog_config,
    )
    # Save
    if args.to_remote:
        asyncio.run(generator.write_to_api(href=args.to_remote))
        print(f"Catalog successfully pushed to {args.to_remote}")
    if args.to_local:
        generator.generate_catalog_and_save(href=args.to_local)
        print(f"Catalog successfully save to {args.to_local}")


if __name__ == "__main__":
    run_cli()
