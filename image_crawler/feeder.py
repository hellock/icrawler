# -*- encoding: utf-8 -*-

import logging
import threading


class Feeder(object):

    def __init__(self, url_queue, session):
        self.url_queue = url_queue
        self.session = session
        self.threads = []
        self.set_logger()

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def feed(self, **kwargs):
        pass

    def create_threads(self, **kwargs):
        self.threads = []
        for i in range(self.thread_num):
            name = 'feeder-{:0>2d}'.format(i+1)
            t = threading.Thread(name=name, target=self.feed, kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def start(self, thread_num, **kwargs):
        self.thread_num = thread_num
        self.create_threads(**kwargs)
        self.lock = threading.Lock()
        for t in self.threads:
            t.start()
            self.logger.info('thread %s started', t.name)

    def __exit__(self):
        self.logger.info('all feeder threads exited')


class SimpleSEFeeder(Feeder):

    def feed(self, url_template, keyword, offset, max_num, page_step):
        print('simple')
        for i in range(offset, offset + max_num, page_step):
            url = url_template.format(keyword, i)
            self.url_queue.put(url)
            self.logger.debug('put url to url_queue: {}'.format(url))
