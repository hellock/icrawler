# -*- coding: utf-8 -*-

import logging
import threading
import time
from requests import exceptions
from six.moves import queue
from six.moves.urllib.parse import urlsplit

from .utils import DupFilter


class Parser(object):

    def __init__(self, url_queue, task_queue, signal, session, dup_filter_size=0):
        self.url_queue = url_queue
        self.task_queue = task_queue
        self.global_signal = signal
        self.session = session
        self.dup_filter = DupFilter(dup_filter_size)
        self.threads = []
        self.set_logger()

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def parse(self, response, **kwargs):
        task = {}
        self.put_task_into_queue(task)

    def put_task_into_queue(self, task):
        if self.dup_filter.check_dup(task):
            self.logger.debug('duplicated task: %s', task['img_url'])
        else:
            self.task_queue.put(task)

    def create_threads(self, **kwargs):
        self.threads = []
        for i in range(self.thread_num):
            name = 'parser-{:0>2d}'.format(i+1)
            t = threading.Thread(name=name, target=self.thread_run, kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def start(self, thread_num, dup_filter_size=0, **kwargs):
        self.dup_filter = DupFilter(dup_filter_size)
        self.thread_num = thread_num
        self.create_threads(**kwargs)
        self.lock = threading.Lock()
        for t in self.threads:
            t.start()
            self.logger.info('thread %s started', t.name)

    def thread_run(self, queue_timeout=2, request_timeout=5, max_retry=3,
                   task_threshold=50, **kwargs):
        while True:
            if self.global_signal.get('reach_max_num'):
                self.logger.info('downloaded image reached max num, thread %s exit',
                                 threading.current_thread().name)
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
                    self.logger.info('no more page urls to parse, thread %s exit',
                                     threading.current_thread().name)
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
                except exceptions.ConnectionError:
                    self.logger.error('Connection error when fetching page %s, '
                                      'remaining retry time: %d', url, retry - 1)
                except exceptions.HTTPError:
                    self.logger.error('HTTP error when fetching page %s, '
                                      'remaining retry time: %d', url, retry - 1)
                except exceptions.Timeout:
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
        for t in self.threads:
            if t.is_alive():
                return True
        return False

    def __exit__(self):
        logging.info('all parser threads exited')
