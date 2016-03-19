# -*- encoding: utf-8 -*-

import os
import queue
import requests
import threading


class Downloader(threading.Thread):

    fetched_num = 0
    max_num = 0
    signal_term = False

    def __init__(self, name, task_queue, lock, img_dir, session, logger):
        threading.Thread.__init__(self, name=name, daemon=True)
        self.task_queue = task_queue
        self.lock = lock
        self.img_dir = img_dir
        self.session = session
        self.logger = logger

    @classmethod
    def clear_status(cls):
        cls.fetched_num = 0
        cls.signal_term = False

    def set_file_path(self, img_task):
        filename = os.path.join(self.img_dir,
                                '{:0>6d}.jpg'.format(self.__class__.fetched_num))
        return filename

    def _reach_max_num(self):
        if (self.__class__.max_num > 0 and
           self.__class__.fetched_num >= self.__class__.max_num):
            return True
        else:
            return False

    def download(self, img_task):
        img_url = img_task['img_url']
        try:
            response = self.session.get(img_url, timeout=10)
        except requests.exceptions.ConnectionError:
            self.logger.error('Connection error when downloading '
                              'image {}'.format(img_url))
        except requests.exceptions.HTTPError:
            self.logger.error('HTTP error when downloading '
                              'image {}'.format(img_url))
        except requests.exceptions.Timeout:
            self.logger.error('Timeout when downloading '
                              'image {}'.format(img_url))
        except:
            self.logger.error('Other error catched when downloading '
                              'image {}'.format(img_url))
        else:
            if self._reach_max_num():
                with self.lock:
                    self.__class__.signal_term = True
                return
            with self.lock:
                self.__class__.fetched_num += 1
            self.logger.info('image #{}\t{}'.format(self.__class__.fetched_num,
                                                    img_url))
            filename = self.set_file_path(img_task)
            with open(filename, 'wb') as fout:
                fout.write(response.content)

    def run(self):
        while True:
            if self.__class__.signal_term:
                break
            try:
                task = self.task_queue.get(timeout=10)
            except queue.Empty:
                with self.lock:
                    self.logger.error('timeout, thread %s exit' % self.name)
                break
            except:
                with self.lock:
                    self.logger.error('exception in thread %s' % (self.name))
            else:
                self.download(task)
                self.task_queue.task_done()
