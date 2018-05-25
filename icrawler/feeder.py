# -*- coding: utf-8 -*-

import os.path as osp
from threading import current_thread

from icrawler.utils import ThreadPool


class Feeder(ThreadPool):
    """Base class for feeder.

    A thread pool of feeder threads, in charge of feeding urls to parsers.

    Attributes:
        thread_num (int): An integer indicating the number of threads.
        global_signal (Signal): A :class:`Signal` object for communication
            among all threads.
        out_queue (Queue): A queue connected with parsers' inputs,
            storing page urls.
        session (Session): A session object.
        logger (Logger): A logging.Logger object used for logging.
        workers (list): A list storing all the threading.Thread objects
            of the feeder.
        lock (Lock): A :class:`Lock` instance shared by all feeder threads.
    """

    def __init__(self, thread_num, signal, session):
        """Init Feeder with some shared variables."""
        super(Feeder, self).__init__(
            thread_num=thread_num, in_queue=None, name='feeder')
        self.signal = signal
        self.session = session

    def feed(self, **kwargs):
        """Feed urls.

        This method should be implemented by users.
        """
        raise NotImplementedError

    def worker_exec(self, **kwargs):
        """Target function of workers"""
        self.feed(**kwargs)
        self.logger.info('thread {} exit'.format(current_thread().name))

    def __exit__(self):
        self.logger.info('all feeder threads exited')


class UrlListFeeder(Feeder):
    """Url list feeder which feed a list of urls"""

    def feed(self, url_list, offset=0, max_num=0):
        if isinstance(url_list, str):
            if osp.isfile(url_list):
                with open(url_list, 'r') as fin:
                    url_list = [line.rstrip('\n') for line in fin]
            else:
                raise IOError('url list file {} not found'.format(url_list))
        elif not isinstance(url_list, list):
            raise TypeError('"url_list" can only be a filename or a str list')

        if offset < 0 or offset >= len(url_list):
            raise ValueError('"offset" exceed the list length')
        else:
            if max_num > 0:
                end_idx = min(len(url_list), offset + max_num)
            else:
                end_idx = len(url_list)
            for i in range(offset, end_idx):
                url = url_list[i]
                self.out_queue.put(url)
                self.logger.debug('put url to url_queue: {}'.format(url))


class SimpleSEFeeder(Feeder):
    """Simple search engine like Feeder"""

    def feed(self, url_template, keyword, offset, max_num, page_step):
        """Feed urls once

        Args:
            url_template: A string with parameters replaced with "{}".
            keyword: A string indicating the searching keyword.
            offset: An integer indicating the starting index.
            max_num: An integer indicating the max number of images to be crawled.
            page_step: An integer added to offset after each iteration.
        """
        for i in range(offset, offset + max_num, page_step):
            url = url_template.format(keyword, i)
            self.out_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))
