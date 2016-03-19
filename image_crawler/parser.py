# -*- encoding: utf-8 -*-

import logging
import threading
from requests import exceptions
import queue


class Parser(object):

    def __init__(self, url_queue, task_queue, session):
        self.url_queue = url_queue
        self.task_queue = task_queue
        self.session = session
        self.threads = []
        self.set_logger()

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, response):
        task = {}
        self.task_queue.put(task)

    def create_threads(self, **kwargs):
        self.threads = []
        for i in range(self.thread_num):
            name = 'parser-{:0>2d}'.format(i+1)
            t = threading.Thread(name=name, target=self.thread_run, kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def start(self, thread_num, **kwargs):
        self.thread_num = thread_num
        self.create_threads(**kwargs)
        self.lock = threading.Lock()
        for t in self.threads:
            t.start()
            self.logger.info('thread %s started', t.name)

    def thread_run(self, queue_timeout=1, request_timeout=5):
        while not self.url_queue.empty():
            # get the page url
            try:
                url = self.url_queue.get(timeout=queue_timeout)
            except queue.Empty:
                self.logger.error('timeout, thread %s exit',
                                  threading.current_thread().name)
                break
            except:
                self.logger.error('exception in thread %s',
                                  threading.current_thread().name)
                continue
            else:
                self.logger.debug('start downloading page {}'.format(url))
            # fetch and parse the page
            try:
                response = self.session.get(url, timeout=request_timeout)
            except exceptions.ConnectionError:
                self.logger.error('Connection error when fetching '
                                  'page %s', url)
            except exceptions.HTTPError:
                self.logger.error('HTTP error when fetching '
                                  'page %s', url)
            except exceptions.Timeout:
                self.logger.error('Timeout when fetching '
                                  'page %s', url)
            except:
                self.logger.error('Other error catched when fetching '
                                  'page %s', url)
            else:
                self.logger.info('parsing result page {}'.format(url))
                self.parse(response.content)

    def __exit__(self):
        logging.info('all parser threads exited')
