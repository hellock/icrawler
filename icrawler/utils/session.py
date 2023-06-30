from urllib.parse import urlsplit

import requests


class Session(requests.Session):
    def __init__(self, proxy_pool):
        super().__init__()
        self.proxy_pool = proxy_pool

    def _url_scheme(self, url):
        return urlsplit(url).scheme

    def get(self, url, **kwargs):
        proxy = self.proxy_pool.get_next(protocol=self._url_scheme(url))
        if proxy is None:
            return super().get(url, **kwargs)
        try:
            response = super().get(url, proxies=proxy.format(), **kwargs)
        except requests.exceptions.ConnectionError:
            self.proxy_pool.decrease_weight(proxy)
            raise
        except:
            raise
        else:
            self.proxy_pool.increase_weight(proxy)
            return response

    def post(self, url, data=None, json=None, **kwargs):
        proxy = self.proxy_pool.get_next(protocol=self._url_scheme(url))
        if proxy is None:
            return super().get(url, data, json, **kwargs)
        try:
            response = super().post(url, data, json, proxies=proxy.format(), **kwargs)
        except requests.exceptions.ConnectionError:
            self.proxy_pool.decrease_weight(proxy)
            raise
        except:
            raise
        else:
            self.proxy_pool.increase_weight(proxy)
            return response
