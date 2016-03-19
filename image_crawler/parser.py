# -*- encoding: utf-8 -*-

import logging
import threading


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
            url = self.url_queue.get(timeout=queue_timeout)
            self.logger.debug('start downloading page {}'.format(url))
            response = self.session.get(url, timeout=request_timeout)
            self.logger.info('parsing result page {}'.format(url))
            self.parse(response.content)

    def __exit__(self):
        logging.info('all parser threads exited')
