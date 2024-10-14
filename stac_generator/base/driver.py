import abc
from typing import Any

import httpx

from stac_generator.base.schema import SourceConfig


class IODriver:
    """Base driver for handling IO for different file formats/extensions

    The primary purpose of this class is to enable reading source file from location specified in
    the source config. File can either be read locally or via sending a request to the hosting server.
    """

    def __init__(self, config: SourceConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def get_data(self) -> Any:
        """Read data based on config information"""
        raise NotImplementedError

    @staticmethod
    def fetch(config: SourceConfig) -> httpx.Response:
        """Use config information to send a GET request to an endpoint

        :param config: config information containing the url and request headers
        :type config: SourceConfig
        :return: raw Response object
        :rtype: httpx.Response
        """
        return httpx.request(
            method=str(config.method),
            url=str(config.location),
            params=config.params,
            headers=config.headers,
            json=config.json_body,
            cookies=config.cookies,
            content=config.content,
            data=config.data,
        )
