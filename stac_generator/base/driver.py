import abc
from typing import Any

import httpx

from stac_generator.base.schema import SourceConfig


class IODriver:
    def __init__(self, config: SourceConfig) -> None:
        self.config = config

    @abc.abstractmethod
    def get_data(self) -> Any:
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
