import logging

from stac_generator.factory import StacGeneratorFactory

__all__ = ("StacGeneratorFactory",)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)
