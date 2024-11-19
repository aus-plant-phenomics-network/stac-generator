import logging

from stac_generator.factory import StacGeneratorFactory

__all__ = ("StacGeneratorFactory",)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

for _ in logging.root.manager.loggerDict:
    logging.getLogger(_).disabled = True
