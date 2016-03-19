# -*- encoding: utf-8 -*-

import threading


class Parser(threading.Thread):

    url_cnt = 0

    def __init__(self, name, start_urls, task_queue, lock, session, logger):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.start_urls = start_urls
        self.task_queue = task_queue
        self.lock = lock
        self.session = session
        self.logger = logger

    def parse(self, response):
        task = {}
        self.task_queue.put(task)

    def run(self):
        while self.__class__.url_cnt < len(self.start_urls):
            url = self.start_urls[self.__class__.url_cnt]
            with self.lock:
                self.__class__.url_cnt += 1
            response = self.session.get(url)
            self.logger.info('parsing result page {}'.format(url))
            self.parse(response.content)
