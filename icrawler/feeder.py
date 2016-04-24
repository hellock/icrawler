# -*- coding: utf-8 -*-

import logging
import threading

from .utils import DupFilter


class Feeder(object):
    """Base class for feeders.

    Essentially a thread manager, in charge of feeding urls to parses.

    Attributes:
        url_queue: A queue storing page urls, connecting Feeder and Parser.
        global_signal: A Signal object for cross-module communication.
        session: A requests.Session object.
        logger: A logging.Logger object used for logging.
        dup_filter: A DupFilter object used for filtering urls.
        threads: A list storing all the threading.Thread objects of the feeder.
        thread_num: An integer indicating the number of threads.
        lock: A threading.Lock object.
    """

    def __init__(self, url_queue, signal, session):
        """Init Feeder with some shared variables."""
        self.url_queue = url_queue
        self.global_signal = signal
        self.session = session
        self.threads = []
        self.set_logger()

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def feed(self, **kwargs):
        """Feed urls.

        This method should be overridden by users.
        """
        pass

    def put_url_into_queue(self, url):
        """Safely put an url into the url_queue.

        Before putting the url into the queue, DupFilter.check_dup() method
        will be called. If the url is duplicated, then it will be discarded.

        Args:
            url: The page url string.
        """
        if self.dup_filter.check_dup(url):
            self.logger.debug('duplicated url: %s', url)
        else:
            self.url_queue.put(url)

    def create_threads(self, **kwargs):
        """Create feeder threads.

        Creates threads named "feeder-xx" counting from 01 to 99, all threads
        are daemon threads.

        Args:
            **kwargs: Arguments to be passed to the thread_run() method.
        """
        self.threads = []
        for i in range(self.thread_num):
            name = 'feeder-{:0>2d}'.format(i + 1)
            t = threading.Thread(name=name, target=self.thread_run,
                                 kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def thread_run(self, **kwargs):
        """Target method of threads.

        By default, this method just calls feed() method.

        Args:
            **kwargs: Arguments to be passed to the feed() method.
        """
        self.feed(**kwargs)

    def start(self, thread_num, dup_filter_size=0, **kwargs):
        """Start all the feeder threads.

        Args:
            thread_num: An integer indicating the number of threads to be
                        created and run.
            dup_filter_size: An integer deciding the cache size of dup_filter.
            **kwargs: Arguments to be passed to the create_threads() method.
        """
        self.dup_filter = DupFilter(dup_filter_size)
        self.thread_num = thread_num
        self.create_threads(**kwargs)
        self.lock = threading.Lock()
        for t in self.threads:
            t.start()
            self.logger.info('thread %s started', t.name)

    def is_alive(self):
        """Check if the feeder has active threads.

        Returns:
            A boolean indicating if at least one thread is alive.
        """
        for t in self.threads:
            if t.is_alive():
                return True
        return False

    def __exit__(self):
        self.logger.info('all feeder threads exited')


class SimpleSEFeeder(Feeder):
    """Simple search-engine-like Feeder"""

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
            self.url_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))
