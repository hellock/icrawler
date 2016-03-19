# -*- coding: utf-8 -*-

from .downloader import Downloader
import logging
import os
from .parser import Parser
import queue
import requests
import threading


class ImageCrawler(object):
    """
    Base class for image crawlers

    This class contains basic interfaces for image crawls
    and can only be inherited.

    """

    def __init__(self, img_dir='images', parser_cls=Parser,
                 downloader_cls=Downloader):
        self.img_dir = img_dir
        if not os.path.isdir(img_dir):
            os.makedirs(img_dir)
        self.crawl_done = False
        self.start_urls = []
        self.task_queue = queue.Queue()
        self.fetched_num = 0
        self.max_num = 0
        self.parser_cls = parser_cls
        self.downloader_cls = downloader_cls
        self.headers = {
            'User-Agent': ('Mozilla/5.0 (Macintosh; Intel Mac OS X '
                           '10_11_3) AppleWebKit/537.36 (KHTML, like Gecko) '
                           'Chrome/48.0.2564.116 Safari/537.36')
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self._set_logger()

    def _set_logger(self):
        self.logger = logging.getLogger(
            self.__class__.__name__ + str(hash(self)))
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(logging.StreamHandler())

    def prepare(self, *args, **kwargs):
        pass

    def parse(self, parser_num):
        lock = threading.Lock()
        parser_threads = []
        for i in range(parser_num):
            name = 'parser-{:0>2d}'.format(i+1)
            parser = self.parser_cls(name, self.start_urls, self.task_queue,
                                     lock, self.session, self.logger)
            parser_threads.append(parser)
        for parser in parser_threads:
            parser.start()
            with lock:
                self.logger.info('thread %s started' % parser.name)

    def fetch_image(self, downloader_num, max_num=0):
        lock = threading.Lock()
        downloader_threads = []
        Downloader.max_num = max_num
        for i in range(downloader_num):
            name = 'downloader-{:0>2d}'.format(i+1)
            downloader = self.downloader_cls(name, self.task_queue, lock,
                                             self.img_dir, self.session, self.logger)
            downloader_threads.append(downloader)
        for downloader in downloader_threads:
            downloader.start()
            with lock:
                self.logger.info('thread %s started' % downloader.name)

    def crawl(self, parser_num=1, downloader_num=1, max_num=0, *args, **kwargs):
        self.downloader_cls.clear_status()
        self.prepare(max_num, *args, **kwargs)
        self.logger.info('start crawling...')
        self.parse(parser_num)
        self.fetch_image(downloader_num, max_num)
        while True:
            if threading.active_count() > 1:
                pass
            else:
                break
        self.logger.info('All images downloaded!')
