# -*- coding: utf-8 -*-

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
    """Base class for Crawlers.

    Attributes:
        save_dir: The root folder where images will be saved.
        url_queue: A queue storing page urls, connecting Feeder and Parser.
        task_queue: A queue storing image downloading tasks, connecting
                    Parser and Downloader.
        session: A requests.Session object.
        feeder: A Feeder object.
        parser: A Parser object.
        downloader: A Downloader object.
        signal: A Signal object shared by feeder, parser and downloader, used
                for cross-module communication.
        logger: A logging.Logger object used for logging.
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
        """Init Crawler with class names and other arguments.

        Args:
            img_dir: The root folder where images will be saved.
            feeder_cls: Class of the feeder used in the crawler.
            parser_cls: Class of the parser used in the crawler.
            downloader_cls: Class of the downloader used in the crawler.
            feeder_threads: number of feeder threads.
            parser_threads: number of parser threads.
            downloader_threads: number of downloader threads.
            log_level: logging level for the logger.
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
        """Init signal.

        3 signals are added: feeder_exited, parser_exited and reach_max_num.
        """
        self.signal = Signal()
        self.signal.set(feeder_exited=False,
                        parser_exited=False,
                        reach_max_num=False)

    def set_storage(self, storage):
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

        By default no proxy is scanned or loaded.
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
        """Start crawling.

        Args:
            feeder_kwargs: Arguments to be passed to feeder.start()
            parser_kwargs: Arguments to be passed to parser.start()
            downloader_kwargs: Arguments to be passed to downloader.start()
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
            if threading.active_count() <= 1:
                break
            if not self.feeder.is_alive():
                self.signal.set(feeder_exited=True)
            if not self.parser.is_alive():
                self.signal.set(parser_exited=True)
            time.sleep(1)
        self.logger.info('Crawling task done!')
