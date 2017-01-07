How to use proxies
==================

A powerful ``ProxyPool`` class is provided to handle the proxies. You
will need to override the ``Crawler.set_proxy_pool()`` method to use it.

If you just need a few (for example less than 30) proxies, you can
override it like the following.

.. code:: python

    def set_proxy_pool(self):
        self.proxy_pool = ProxyPool()
        self.proxy_pool.default_scan(region='overseas', expected_num=10,
                                     out_file='proxies.json')

Then it will scan 10 valid overseas (out of mainland China) proxies and
automatically use these proxies to request pages and images.

If you have special requirements on proxies, you can use ProxyScanner
and write your own scan functions to satisfy your demands.

.. code:: python

    def set_proxy_pool(self):
        proxy_scanner = ProxyScanner()
        proxy_scanner.register_func(proxy_scanner.scan_file,
                                    {'src_file': 'proxy_overseas.json'})
        proxy_scanner.register_func(your_own_scan_func,
                                    {'arg1': '', 'arg2': ''})
        self.proxy_pool.scan(proxy_scanner, expected_num=10, out_file='proxies.json')

Every time when making a new request, a proxy will be selected from the
pool. Each proxy has a weight from 0.0 to 1.0, if a proxy has a greater
weight, it has more chance to be selected for a request. The weight is
increased or decreased automatically according to the rate of successful
connection.