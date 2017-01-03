# -*- coding: utf-8 -*-

import logging
import time
from threading import current_thread

from six.moves import queue
from six.moves.urllib.parse import urlsplit

from icrawler.utils import ThreadPool


class Parser(ThreadPool):
    """Base class for parses.

    Essentially a thread manager, in charge of downloading pages, parsing pages,
    extracting image urls and put them into task_queue.

    Attributes:
        url_queue: A queue storing page urls, connecting Feeder and Parser.
        task_queue: A queue storing image downloading tasks, connecting
                    Parser and Downloader.
        global_signal: A Signal object for cross-module communication.
        session: A requests.Session object.
        logger: A logging.Logger object used for logging.
        threads: A list storing all the threading.Thread objects of the parser.
        thread_num: An integer indicating the number of threads.
        lock: A threading.Lock object.
    """

    def __init__(self, thread_num, signal, session):
        """Init Parser with some shared variables."""
        super(Parser, self).__init__(thread_num, name='parser')
        self.signal = signal
        self.session = session

    def parse(self, response, **kwargs):
        """Parse a page and extract image urls, then put it into task_queue.

        This method should be overridden by users.
        example: task = {}
                 self.out_queue.put(task)
        """
        raise NotImplementedError

    def worker_exec(self,
                    queue_timeout=2,
                    req_timeout=5,
                    max_retry=3,
                    **kwargs):
        """Target method of threads.

        Firstly download the page and then call the parse() method. A parser
        thread will exit in either of the following cases:
        1. All feeder threads have exited and the url_queue is empty.
        2. Downloaded image number has reached required number(max_num).

        Args:
            queue_timeout: An integer indicating the timeout of getting
                           urls from url_queue.
            req_timeout: An integer indicating the timeout of making
                              requests for downloading pages.
            max_retry: An integer setting the max retry times if request fails.
            **kwargs: Arguments to be passed to the feed() method.
        """
        while True:
            if self.signal.get('reach_max_num'):
                self.logger.info('downloaded image reached max num, thread %s '
                                 'is ready to exit', current_thread().name)
                break
            # get the page url
            try:
                url = self.in_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.signal.get('feeder_exited'):
                    self.logger.info(
                        'no more page urls for thread %s to parse',
                        current_thread().name)
                    break
                else:
                    self.logger.info('%s is waiting for new page urls',
                                     current_thread().name)
                    continue
            except:
                self.logger.error('exception in thread %s',
                                  current_thread().name)
                continue
            else:
                self.logger.debug('start fetching page {}'.format(url))
            # fetch and parse the page
            retry = max_retry
            while retry > 0:
                try:
                    base_url = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
                    response = self.session.get(url,
                                                timeout=req_timeout,
                                                headers={'Referer': base_url})
                except Exception as e:
                    self.logger.error(
                        'Exception caught when fetching page %s, '
                        'error: %s, remaining retry times: %d', url, e,
                        retry - 1)
                else:
                    self.logger.info('parsing result page {}'.format(url))
                    for task in self.parse(response, **kwargs):
                        while not self.signal.get('reach_max_num'):
                            try:
                                if isinstance(task, dict):
                                    self.output(task, timeout=1)
                                elif isinstance(task, str):
                                    # this case only work for GreedyCrawler,
                                    # which need to feed the url back to
                                    # url_queue, dirty implementation
                                    self.input(task, timeout=1)
                            except queue.Full:
                                time.sleep(1)
                            except Exception as e:
                                self.logger.error(
                                    'Exception caught when put task %s into '
                                    'queue, error: %s', task, url)
                            else:
                                break
                        if self.signal.get('reach_max_num'):
                            break
                    self.in_queue.task_done()
                    break
                finally:
                    retry -= 1
        self.logger.info('thread {} exit'.format(current_thread().name))

    def __exit__(self):
        logging.info('all parser threads exited')
