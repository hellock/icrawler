# -*- encoding: utf-8 -*-

import logging
import os
import queue
import requests
import threading


class Downloader(object):

    def __init__(self, img_dir, task_queue, session):
        self.task_queue = task_queue
        self.img_dir = img_dir
        self.session = session
        self.threads = []
        self.clear_status()
        self.set_logger()

    def clear_status(self):
        self.fetched_num = 0
        self.signal_term = False

    def set_logger(self):
        self.logger = logging.getLogger(__name__)

    def set_file_path(self, img_task):
        filename = os.path.join(self.img_dir,
                                '{:0>6d}.jpg'.format(self.fetched_num))
        return filename

    def reach_max_num(self):
        if (self.max_num > 0 and self.fetched_num >= self.max_num):
            return True
        else:
            return False

    def download(self, img_task, request_timeout):
        img_url = img_task['img_url']
        try:
            response = self.session.get(img_url, timeout=request_timeout)
        except requests.exceptions.ConnectionError:
            self.logger.error('Connection error when downloading '
                              'image %s', img_url)
        except requests.exceptions.HTTPError:
            self.logger.error('HTTP error when downloading '
                              'image %s', img_url)
        except requests.exceptions.Timeout:
            self.logger.error('Timeout when downloading '
                              'image %s', img_url)
        except:
            self.logger.error('Other error catched when downloading '
                              'image %s', img_url)
        else:
            if self.reach_max_num():
                with self.lock:
                    self.signal_term = True
                return
            with self.lock:
                self.fetched_num += 1
            self.logger.info('image #%s\t%s', self.fetched_num, img_url)
            filename = self.set_file_path(img_task)
            with open(filename, 'wb') as fout:
                fout.write(response.content)

    def process_meta(self, img_task):
        pass

    def create_threads(self, **kwargs):
        self.threads = []
        for i in range(self.thread_num):
            name = 'downloader-{:0>2d}'.format(i+1)
            t = threading.Thread(name=name, target=self.thread_run, kwargs=kwargs)
            t.daemon = True
            self.threads.append(t)

    def start(self, thread_num, **kwargs):
        self.thread_num = thread_num
        self.clear_status()
        self.create_threads(**kwargs)
        self.lock = threading.Lock()
        for t in self.threads:
            t.start()
            self.logger.info('thread %s started', t.name)

    def thread_run(self, max_num, queue_timeout=20, request_timeout=10):
        self.max_num = max_num
        while True:
            if self.signal_term:
                break
            try:
                task = self.task_queue.get(timeout=queue_timeout)
            except queue.Empty:
                self.logger.error('timeout, thread %s exit',
                                  threading.current_thread().name)
                break
            except:
                self.logger.error('exception in thread %s',
                                  threading.current_thread().name)
            else:
                self.download(task, request_timeout)
                self.process_meta(task)
                self.task_queue.task_done()

    def __exit__(self):
        self.logger.info('all downloader threads exited')
