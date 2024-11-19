import logging

from stac_generator.factory import StacGeneratorFactory

__all__ = ("StacGeneratorFactory",)

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

for name in logging.root.manager.loggerDict:
    if not name.startswith(__name__):
        logging.getLogger(name).disabled = True
