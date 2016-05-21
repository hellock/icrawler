# -*- coding: utf-8 -*-

import logging
import os
import sys
import threading
import time
from six.moves import queue

from .downloader import Downloader
from .feeder import Feeder
from .parser import Parser
from .utils import Signal
from .utils import ProxyPool
from .utils import Session


class Crawler(object):
    """Base class for Crawlers.

    Attributes:
        img_dir: The root folder where images will be saved.
        url_queue: A queue storing page urls, connecting Feeder and Parser.
        task_queue: A queue storing image downloading tasks, connecting
                    Parser and Downloader.
        headers: A dict of request headers used by session.
        session: A requests.Session object.
        feeder: A Feeder object.
        parser: A Parser object.
        downloader: A Downloader object.
        signal: A Signal object shared by feeder, parser and downloader, used
                for cross-module communication.
        logger: A logging.Logger object used for logging.
    """

    def __init__(self, img_dir='images', feeder_cls=Feeder, parser_cls=Parser,
                 downloader_cls=Downloader, log_level=logging.INFO):
        """Init Crawler with class names and other arguments.

        Args:
            img_dir: The root folder where images will be saved.
            feeder_cls: Class of the feeder used in the crawler.
            parser_cls: Class of the parser used in the crawler.
            downloader_cls: Class of the downloader used in the crawler.
            log_level: logging level for the logger.
        """
        self.img_dir = img_dir
        if not os.path.isdir(img_dir):
            os.makedirs(img_dir)
        # init queues
        self.url_queue = queue.Queue()
        self.task_queue = queue.Queue()
        # set logger
        self.set_logger(log_level)
        # set proxy pool
        self.set_proxy_pool()
        # set session
        self.set_session()
        # init signal
        self.init_signal()
        # set feeder, parser and downloader
        self.feeder = feeder_cls(self.url_queue, self.signal, self.session)
        self.parser = parser_cls(self.url_queue, self.task_queue,
                                 self.signal, self.session)
        self.downloader = downloader_cls(self.img_dir, self.task_queue,
                                         self.signal, self.session)

    def init_signal(self):
        """Init signal.

        3 signals are added: feeder_exited, parser_exited and reach_max_num.
        """
        self.signal = Signal()
        self.signal.set({'feeder_exited': False,
                         'parser_exited': False,
                         'reach_max_num': False})

    def set_proxy_pool(self):
        """Construct a proxy pool

        By default no proxy is scaned or loaded, you will have to override this
        method if you want to use proxies.
        """
        self.proxy_pool = ProxyPool()

    def set_session(self, headers=None):
        """Init session with default or custom headers

        Args:
            headers: A dict of headers (default None, thus using the default
                     header to init the session)
        """
        if headers is None:
            self.headers = {
                'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X '
                               '10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) '
                               'Chrome/48.0.2564.116 Safari/537.36')
            }
        else:
            self.headers = headers
        self.session = Session(self.proxy_pool)
        self.session.headers.update(self.headers)

    def set_logger(self, log_level):
        """Configure the logger with log_level."""
        logging.basicConfig(
            format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
            level=log_level, stream=sys.stderr)
        self.logger = logging.getLogger(__name__)
        logging.getLogger('requests').setLevel(logging.WARNING)

    def crawl(self, feeder_thread_num=1, parser_thread_num=1,
              downloader_thread_num=1, feeder_kwargs={},
              parser_kwargs={}, downloader_kwargs={}):
        """Start crawling.

        Args:
            feeder_thread_num: An integer indicating the number of feeder threads.
            parser_thread_num: An integer indicating the number of parser threads.
            downloader_thread_num: An integer indicating the number of
                                   downloader threads.
            feeder_kwargs: Arguments to be passed to feeder.start()
            parser_kwargs: Arguments to be passed to parser.start()
            downloader_kwargs: Arguments to be passed to downloader.start()
        """
        self.signal.reset()
        self.logger.info('start crawling...')
        self.logger.info('starting feeder... %s threads in total',
                         feeder_thread_num)
        self.feeder.start(feeder_thread_num, **feeder_kwargs)
        self.logger.info('starting parser... %s threads in total',
                         parser_thread_num)
        self.parser.start(parser_thread_num,
                          task_threshold=10 * downloader_thread_num,
                          **parser_kwargs)
        self.logger.info('starting downloader... %s threads in total',
                         downloader_thread_num)
        self.downloader.start(downloader_thread_num, **downloader_kwargs)
        while True:
            if threading.active_count() <= 1:
                break
            if not self.feeder.is_alive():
                self.signal.set({'feeder_exited': True})
            if not self.parser.is_alive():
                self.signal.set({'parser_exited': True})
            time.sleep(1)
        self.logger.info('Crawling task done!')
