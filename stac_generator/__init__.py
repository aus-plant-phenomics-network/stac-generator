import logging

from stac_generator.factory import StacGeneratorFactory

__all__ = ("StacGeneratorFactory",)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
