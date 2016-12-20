# -*- coding: utf-8 -*-

import logging
import threading
import time

from requests.exceptions import ConnectionError, HTTPError, Timeout
from six.moves import queue
from six.moves.urllib.parse import urlsplit

from icrawler.utils import DupFilter


class Parser(object):
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
        dup_filter: A DupFilter object used for filtering urls.
        threads: A list storing all the threading.Thread objects of the parser.
        thread_num: An integer indicating the number of threads.
        lock: A threading.Lock object.
    """

    def __init__(self, url_queue, task_queue, signal, session):
        """Init Parser with some shared variables."""
        self.url_queue = url_queue
        self.task_queue = task_queue
        self.global_signal = signal
        self.session = session
        self.threads = []
        self.set_logger()

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, response, **kwargs):
        """Parse a page and extract image urls, then put it into task_queue.

        This method should be overridden by users.
        example: task = {}
                 self.put_task_into_queue(task)
        """
        raise NotImplementedError

    def put_task_into_queue(self, task):
        """Safely put an downloading task into the task_queue.

        Before putting the task into the queue, DupFilter.check_dup() method
        will be called. If the task is duplicated, then it will be discarded.

        Args:
            task: A dict containing downloading task info. The dict must
                  contain a field named "img_url" and other fields are optional
                  and rely on the user's demands.
                  For example:
                  {'img_url': 'http://www.example.com/abc.jpg',
                   'tags': ['tag1', 'tag2'],
                   'label': True}
        """
        if self.dup_filter.check_dup(task):
            self.logger.debug('duplicated task: %s', task['img_url'])
        else:
            self.task_queue.put(task)

    def create_threads(self, **kwargs):
        """Create parser threads.

        Creates threads named "parser-xx" counting from 01 to 99, all threads
        are daemon threads.

        Args:
            **kwargs: Arguments to be passed to the thread_run() method.
        """
        self.threads = []
        for i in range(self.thread_num):
            name = 'parser-{:0>2d}'.format(i + 1)
            t = threading.Thread(name=name, target=self.thread_run,
                                 kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def start(self, thread_num, dup_filter_size=0, **kwargs):
        """Start all the parser threads.

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

    def thread_run(self, queue_timeout=2, request_timeout=5, max_retry=3,
                   task_threshold=50, **kwargs):
        """Target method of threads.

        Firstly download the page and then call the parse() method. A parser
        thread will exit in either of the following cases:
        1. All feeder threads have exited and the url_queue is empty.
        2. Downloaded image number has reached required number(max_num).

        Args:
            queue_timeout: An integer indicating the timeout of getting
                           urls from url_queue.
            request_timeout: An integer indicating the timeout of making
                              requests for downloading pages.
            max_retry: An integer setting the max retry times if request fails.
            task_threshold: An integer setting the threshold of task remaining
                            in the task_queue. When the number of remaining
                            tasks is greater than it, the thread will sleep
                            for one second and check again.
            **kwargs: Arguments to be passed to the feed() method.
        """
        while True:
            if self.global_signal.get('reach_max_num'):
                self.logger.info('downloaded image reached max num, thread %s'
                                 ' exit', threading.current_thread().name)
                break
            # if there is still lots of tasks in the queue, stop parsing
            if self.task_queue.qsize() > task_threshold:
                time.sleep(1)
                continue
            # get the page url
            try:
                url = self.url_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.global_signal.get('feeder_exited'):
                    self.logger.info('no more page urls to parse, thread %s'
                                     ' exit', threading.current_thread().name)
                    break
                else:
                    self.logger.info('%s is waiting for new page urls',
                                     threading.current_thread().name)
                    continue
            except:
                self.logger.error('exception in thread %s',
                                  threading.current_thread().name)
                continue
            else:
                self.logger.debug('start downloading page {}'.format(url))
            # fetch and parse the page
            retry = max_retry
            while retry > 0:
                try:
                    base_url = '{0.scheme}://{0.netloc}'.format(urlsplit(url))
                    response = self.session.get(url, timeout=request_timeout,
                                                headers={'Referer': base_url})
                except ConnectionError:
                    self.logger.error('Connection error when fetching page %s, '
                                      'remaining retry time: %d', url, retry - 1)
                except HTTPError:
                    self.logger.error('HTTP error when fetching page %s, '
                                      'remaining retry time: %d', url, retry - 1)
                except Timeout:
                    self.logger.error('Timeout when fetching page %s, '
                                      'remaining retry time: %d', url, retry - 1)
                except Exception as ex:
                    self.logger.error('Unexcepted error catched when fetching '
                                      'page %s, error info: %s, remaining retry'
                                      ' times: %d', url, ex, retry - 1)
                else:
                    self.logger.info('parsing result page {}'.format(url))
                    self.parse(response, **kwargs)
                    break
                finally:
                    retry -= 1

    def is_alive(self):
        """Check if the parser has active threads.

        Returns:
            A boolean indicating if at least one thread is alive.
        """
        for t in self.threads:
            if t.is_alive():
                return True
        return False

    def __exit__(self):
        logging.info('all parser threads exited')
