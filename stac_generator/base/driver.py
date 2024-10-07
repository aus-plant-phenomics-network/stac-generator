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

    def fetch(self) -> httpx.Response:
        return httpx.request(
            method=str(self.config.method),
            url=str(self.config.location),
            params=self.config.params,
            headers=self.config.headers,
            json=self.config.json,
            cookies=self.config.cookies,
            content=self.config.content,
            data=self.config.data,
        )

    @abc.abstractmethod
    async def read_local(self) -> Any:
        raise NotImplementedError
