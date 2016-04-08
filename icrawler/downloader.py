# -*- coding: utf-8 -*-

import io
import logging
import os
import requests
import threading
from PIL import Image
from six.moves import queue


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
        if self.signal_term:
            return True
        if self.max_num > 0 and self.fetched_num >= self.max_num:
            return True
        else:
            return False

    def _size_smaller(self, sz1, sz2):
        if sz1[0] < sz2[0] and sz1[1] < sz2[1]:
            return True
        else:
            return False

    def _size_greater(self, sz1, sz2):
        if sz1[0] > sz2[0] and sz1[1] > sz2[1]:
            return True
        else:
            return False

    def download(self, img_task, request_timeout, max_retry=3, min_size=None,
                 max_size=None, **kwargs):
        img_url = img_task['img_url']
        retry = max_retry
        while retry > 0:
            try:
                response = self.session.get(img_url, timeout=request_timeout)
            except requests.exceptions.ConnectionError:
                self.logger.error('Connection error when downloading image %s, '
                                  'remaining retry time: %d', img_url, retry - 1)
            except requests.exceptions.HTTPError:
                self.logger.error('HTTP error when downloading image %s '
                                  'remaining retry time: %d', img_url, retry - 1)
            except requests.exceptions.Timeout:
                self.logger.error('Timeout when downloading image %s '
                                  'remaining retry time: %d', img_url, retry - 1)
            except Exception as ex:
                self.logger.error('Unexcepted error catched when downloading '
                                  'image %s, error info: %s,remaining retry '
                                  'time: %d', img_url, ex, retry - 1)
            else:
                if min_size is not None or max_size is not None:
                    img = Image.open(io.BytesIO(response.content))
                    if min_size is not None and not self._size_greater(img.size, min_size):
                        return
                    elif max_size is not None and not self._size_smaller(img.size, max_size):
                        return
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
                break
            finally:
                retry -= 1

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

    def thread_run(self, max_num, queue_timeout=5, request_timeout=10, **kwargs):
        self.max_num = max_num
        while True:
            if self.signal_term:
                break
            try:
                task = self.task_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if kwargs['parser'].is_alive():
                    self.logger.info('%s is waiting for new download tasks',
                                     threading.current_thread().name)
                else:
                    self.logger.info('no more download task, thread %s exit',
                                     threading.current_thread().name)
                    break
            except:
                self.logger.error('exception in thread %s',
                                  threading.current_thread().name)
            else:
                self.download(task, request_timeout, **kwargs)
                self.process_meta(task)
                self.task_queue.task_done()

    def __exit__(self):
        self.logger.info('all downloader threads exited')
