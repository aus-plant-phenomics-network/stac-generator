from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence

    from stac_pydantic.shared import Provider


def serialise_handler(
    id: str,
    src: str | Sequence[str],
    dst: str,
    title: str | None = "Auto-generated Stac Item",
    description: str | None = "Auto-generated Stac Item",
    license: str | None = None,
    providers: list[Provider] | None = None,
    num_workers: int = 1,
) -> None:
    from concurrent.futures import ProcessPoolExecutor

    from stac_generator.core.base.generator import StacSerialiser
    from stac_generator.core.base.schema import StacCollectionConfig
    from stac_generator.factory import StacGeneratorFactory

    collection_config = StacCollectionConfig(
        id=id,
        title=title,
        description=description,
        license=license,
        providers=providers,
    )

    # Generate
    if num_workers == 1:
        # Use a single thread
        generator = StacGeneratorFactory.get_collection_generator(
            source_configs=src,
            collection_config=collection_config,
        )
        # Save
        serialiser = StacSerialiser(generator, dst)
        serialiser()
    elif num_workers > 1:
        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            generator = StacGeneratorFactory.get_collection_generator(
                source_configs=src,
                collection_config=collection_config,
                pool=executor,
            )
            serialiser = StacSerialiser(generator, dst)
            serialiser()
    else:
        raise ValueError(f"Invalid number of threads: {num_workers}. Must be greater than 0.")
