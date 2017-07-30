# -*- coding: utf-8 -*-
"""Crawler base class"""

import logging
import sys
import threading
import time
from importlib import import_module

from icrawler import Downloader, Feeder, Parser
from icrawler import storage as storage_package
from icrawler.storage import BaseStorage
from icrawler.utils import ProxyPool, Session, Signal


class Crawler(object):
    """Base class for crawlers

    Attributes:
        session (Session): A Session object.
        feeder (Feeder): A Feeder object.
        parser (Parser): A Parser object.
        downloader (Downloader): A Downloader object.
        signal (Signal): A Signal object shared by all components,
                         used for communication among threads
        logger (Logger): A Logger object used for logging
    """

    def __init__(self,
                 feeder_cls=Feeder,
                 parser_cls=Parser,
                 downloader_cls=Downloader,
                 feeder_threads=1,
                 parser_threads=1,
                 downloader_threads=1,
                 storage={'backend': 'FileSystem',
                          'root_dir': 'images'},
                 log_level=logging.INFO):
        """Init components with class names and other arguments.

        Args:
            feeder_cls: class of feeder
            parser_cls: class of parser
            downloader_cls: class of downloader.
            feeder_threads: thread number used by feeder
            parser_threads: thread number used by parser
            downloader_threads: thread number used by downloader
            storage (dict or BaseStorage): storage backend configuration
            log_level: logging level for the logger
        """

        # set logger
        self.set_logger(log_level)
        # set proxy pool
        self.set_proxy_pool()
        # set session
        self.set_session()
        # init signal
        self.init_signal()
        # set storage
        self.set_storage(storage)
        # set feeder, parser and downloader
        self.feeder = feeder_cls(feeder_threads, self.signal, self.session)
        self.parser = parser_cls(parser_threads, self.signal, self.session)
        self.downloader = downloader_cls(downloader_threads, self.signal,
                                         self.session, self.storage)
        # connect all components
        self.feeder.connect(self.parser).connect(self.downloader)

    def init_signal(self):
        """Init signal

        3 signals are added: ``feeder_exited``, ``parser_exited`` and
        ``reach_max_num``.
        """
        self.signal = Signal()
        self.signal.set(feeder_exited=False,
                        parser_exited=False,
                        reach_max_num=False)

    def set_storage(self, storage):
        """Set storage backend for downloader

        For full list of storage backend supported, please see :mod:`storage`.

        Args:
            storage (dict or BaseStorage): storage backend configuration or instance

        """
        if isinstance(storage, BaseStorage):
            self.storage = storage
        elif isinstance(storage, dict):
            if 'backend' not in storage and 'root_dir' in storage:
                storage['backend'] = 'FileSystem'
            try:
                backend_cls = getattr(storage_package, storage['backend'])
            except AttributeError:
                try:
                    backend_cls = import_module(storage['backend'])
                except ImportError:
                    self.logger.error('cannot find backend module %s',
                                      storage['backend'])
                    sys.exit()
            kwargs = storage.copy()
            del kwargs['backend']
            self.storage = backend_cls(**kwargs)
        else:
            raise TypeError('"storage" must be a storage object or dict')

    def set_proxy_pool(self, pool=None):
        """Construct a proxy pool

        By default no proxy is used.

        Args:
            pool (ProxyPool, optional): a :obj:`ProxyPool` object
        """
        self.proxy_pool = ProxyPool() if pool is None else pool

    def set_session(self, headers=None):
        """Init session with default or custom headers

        Args:
            headers: A dict of headers (default None, thus using the default
                     header to init the session)
        """
        if headers is None:
            headers = {
                'User-Agent':
                ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_3)'
                 ' AppleWebKit/537.36 (KHTML, like Gecko) '
                 'Chrome/48.0.2564.116 Safari/537.36')
            }
        elif not isinstance(headers, dict):
            raise TypeError('"headers" must be a dict object')

        self.session = Session(self.proxy_pool)
        self.session.headers.update(headers)

    def set_logger(self, log_level=logging.INFO):
        """Configure the logger with log_level."""
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=log_level,
            stream=sys.stderr)
        self.logger = logging.getLogger(__name__)
        logging.getLogger('requests').setLevel(logging.WARNING)

    def crawl(self, feeder_kwargs={}, parser_kwargs={}, downloader_kwargs={}):
        """Start crawling

        This method will start feeder, parser and download and wait
        until all threads exit.

        Args:
            feeder_kwargs (dict): Arguments to be passed to ``feeder.start()``
            parser_kwargs (dict): Arguments to be passed to ``parser.start()``
            downloader_kwargs (dict): Arguments to be passed to
                ``downloader.start()``
        """
        self.signal.reset()
        self.logger.info('start crawling...')

        self.logger.info('starting %d feeder threads...',
                         self.feeder.thread_num)
        self.feeder.start(**feeder_kwargs)

        self.logger.info('starting %d parser threads...',
                         self.parser.thread_num)
        self.parser.start(**parser_kwargs)

        self.logger.info('starting %d downloader threads...',
                         self.downloader.thread_num)
        self.downloader.start(**downloader_kwargs)

        while True:
            if not self.feeder.is_alive():
                self.signal.set(feeder_exited=True)
            if not self.parser.is_alive():
                self.signal.set(parser_exited=True)
            if not self.downloader.is_alive():
                break
            time.sleep(1)

        if not self.feeder.in_queue.empty():
            self.feeder.clear_buffer()
        if not self.parser.in_queue.empty():
            self.parser.clear_buffer()
        if not self.downloader.in_queue.empty():
            self.downloader.clear_buffer(True)

        self.logger.info('Crawling task done!')
