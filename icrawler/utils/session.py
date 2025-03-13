from __future__ import annotations

import logging
from collections.abc import Mapping
from urllib.parse import urlsplit

import requests
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

from .. import defaults
from .proxy_pool import ProxyPool


class Session(requests.Session):
    def __init__(
        self, proxy_pool: ProxyPool | None = None, headers: Mapping | None = None, cookies: Mapping | None = None
    ):
        super().__init__()
        self.logger = logging.getLogger("cscholars.connection")
        self.proxy_pool = proxy_pool
        if headers is not None:
            self.headers.update(headers)
        if cookies is not None:
            self.cookies.update(cookies)

    def _url_scheme(self, url):
        return urlsplit(url).scheme

    @retry(
        stop=stop_after_attempt(defaults.MAX_RETRIES),
        wait=wait_random_exponential(exp_base=defaults.BACKOFF_BASE),
        retry=retry_if_exception_type(requests.RequestException),
    )
    def request(self, method, url, *args, **kwargs):
        message = f"{method}ing {url}"
        if args and kwargs:
            message += f" with {args} and {kwargs}"
        elif args:
            message += f" with {args}"
        elif kwargs:
            message += f" with {kwargs}"
        self.logger.debug(message)

        if self.proxy_pool is not None:
            proxy = self.proxy_pool.get_next(protocol=self._url_scheme(url))
            self.logger.debug(f"Using proxy: {proxy.format()}")
            try:
                response = super().request(method, url, *args, proxies=proxy.format(), **kwargs)
                self.proxy_pool.increase_weight(proxy)
            except requests.RequestException:
                self.proxy_pool.decrease_weight(proxy)
                raise
        else:
            response = super().request(method, url, *args, **kwargs)

        if "set-cookie" in response.headers:
            self.cookies.update(response.cookies)
        response.raise_for_status()
        return response
