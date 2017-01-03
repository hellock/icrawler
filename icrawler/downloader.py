# -*- coding: utf-8 -*-

import logging
from threading import current_thread

from PIL import Image
from six import BytesIO
from six.moves import queue
from six.moves.urllib.parse import urlparse

from icrawler.utils import ThreadPool


class Downloader(ThreadPool):
    """Base class for downloaders.

    Essentially a thread manager, in charge of downloading images and save
    them in the corresponding paths.

    Attributes:
        img_dir: The root folder where images will be saved.
        task_queue: A queue storing image downloading tasks, connecting
                    Parser and Downloader.
        global_signal: A Signal object for cross-module communication.
        session: A requests.Session object.
        logger: A logging.Logger object used for logging.
        threads: A list storing all the threading.Thread objects of the parser.
        thread_num: An integer indicating the number of threads.
        lock: A threading.Lock object.
    """

    def __init__(self, thread_num, signal, session, storage):
        """Init Parser with some shared variables."""
        super(Downloader, self).__init__(
            thread_num, out_queue=None, name='downloader')
        self.signal = signal
        self.session = session
        self.storage = storage
        self.file_idx_offset = 0
        self.clear_status()

    def clear_status(self):
        """Reset fetched_num to 0."""
        self.fetched_num = 0

    def set_file_idx_offset(self, file_idx_offset=0):
        """Set offset of file index.

        Args:
            file_idx_offset: if set to an integer, the filename will start from
                             `start_idx` + 1.
                             if set to `auto`, the filename will be exist_max + 1;
        """
        if isinstance(file_idx_offset, int):
            self.file_idx_offset = file_idx_offset
        elif file_idx_offset == 'auto':
            self.file_idx_offset = self.storage.max_file_idx()
        else:
            raise ValueError('"file_idx_offset" must be an integer or `auto`')

    def get_filename(self, task, default_ext):
        """Set the path where the image will be saved.

        The default strategy is to use an increasing 6-digit number as
        the filename. You can override this method if you want to set custom
        naming rules. The file extension is kept if it can be obtained from
        the url, otherwise `default_ext` is used as extension.

        Args:
            task: The task dict got from task_queue.

        Output:
            Filename with extension.
        """
        url_path = urlparse(task['file_url'])[2]
        extension = url_path.split('.')[-1] if '.' in url_path else default_ext
        file_idx = self.fetched_num + self.file_idx_offset
        return '{:06d}.{}'.format(file_idx, extension)

    def reach_max_num(self):
        """Check if downloaded images reached max num.

        Returns:
            A boolean indicating if downloaded images reached max num.
        """
        if self.signal.get('reach_max_num'):
            return True
        if self.max_num > 0 and self.fetched_num >= self.max_num:
            return True
        else:
            return False

    def keep_file(self, response, **kwargs):
        return True

    def download(self, task, default_ext, timeout=5, max_retry=3, **kwargs):
        """Download the image and save it to the corresponding path.

        Args:
            task: The task dict got from task_queue.
            timeout: An integer indicating the timeout of making
                             requests for downloading images.
            max_retry: An integer setting the max retry times if request fails.
            **kwargs: reserved arguments for overriding.
        """
        file_url = task['file_url']
        retry = max_retry
        while retry > 0 and not self.signal.get('reach_max_num'):
            try:
                response = self.session.get(file_url, timeout=timeout)
            except Exception as e:
                self.logger.error('Exception caught when downloading file %s, '
                                  'error: %s, remaining retry times: %d',
                                  file_url, e, retry - 1)
            else:
                if self.reach_max_num():
                    self.signal.set(reach_max_num=True)
                    break
                elif response.status_code != 200:
                    self.logger.error('Response status code %d, file %s',
                                      response.status_code, file_url)
                    break
                elif not self.keep_file(response, **kwargs):
                    break
                with self.lock:
                    self.fetched_num += 1
                    filename = self.get_filename(task, default_ext)
                self.logger.info('image #%s\t%s', self.fetched_num, file_url)
                self.storage.write(filename, response.content)
                break
            finally:
                retry -= 1

    def process_meta(self, task):
        """Process some meta data of the images.

        This method should be overridden by users if wanting to do more things
        other than just downloading the image, such as save annotations.

        Args:
            task: The task dict got from task_queue. This method will make
                  use of fields other than 'img_url' in the dict.
        """
        pass

    def start(self, file_idx_offset=0, *args, **kwargs):
        self.clear_status()
        self.set_file_idx_offset(file_idx_offset)
        self.init_workers(*args, **kwargs)
        for worker in self._workers:
            worker.start()
            self.logger.debug('thread %s started', worker.name)

    def worker_exec(self,
                    max_num,
                    default_ext='',
                    queue_timeout=5,
                    req_timeout=5,
                    **kwargs):
        """Target method of threads.

        Get task from task_queue and then download files and process meta data.
        A downloader thread will exit in either of the following cases:
        1. All parser threads have exited and the task_queue is empty.
        2. Downloaded image number has reached required number(max_num).

        Args:
            queue_timeout: An integer indicating the timeout of getting
                           tasks from task_queue.
            req_timeout: An integer indicating the timeout of making
                              requests for downloading pages.
            **kwargs: Arguments to be passed to the download() method.
        """
        self.max_num = max_num
        while True:
            if self.signal.get('reach_max_num'):
                self.logger.info('downloaded images reach max num, thread %s'
                                 ' is ready to exit', current_thread().name)
                break
            try:
                task = self.in_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.signal.get('parser_exited'):
                    self.logger.info('no more download task for thread %s',
                                     current_thread().name)
                    break
                else:
                    self.logger.info('%s is waiting for new download tasks',
                                     current_thread().name)
            except:
                self.logger.error('exception in thread %s',
                                  current_thread().name)
            else:
                self.download(task, default_ext, req_timeout, **kwargs)
                self.process_meta(task)
                self.in_queue.task_done()
        self.logger.info('thread {} exit'.format(current_thread().name))

    def __exit__(self):
        self.logger.info('all downloader threads exited')


class ImageDownloader(Downloader):

    def _size_lt(self, sz1, sz2):
        return sz1[0] < sz2[0] and sz1[1] < sz2[1]

    def _size_gt(self, sz1, sz2):
        return sz1[0] > sz2[0] and sz1[1] > sz2[1]

    def keep_file(self, response, min_size=None, max_size=None):
        print(min_size)
        try:
            img = Image.open(BytesIO(response.content))
        except (IOError, OSError):
            return False
        if min_size and not self._size_gt(img.size, min_size):
            return False
        if max_size and not self._size_lt(img.size, max_size):
            return False
        return True

    def worker_exec(self,
                    max_num,
                    default_ext='jpg',
                    queue_timeout=5,
                    req_timeout=5,
                    **kwargs):
        super(ImageDownloader, self).worker_exec(
            max_num, default_ext, queue_timeout, req_timeout, **kwargs)

    # def download(self,
    #              task,
    #              default_ext='jpg',
    #              timeout=5,
    #              max_retry=3,
    #              min_size=None,
    #              max_size=None):
    #     print(task, default_ext, timeout)
    #     super(ImageDownloader, self).download(
    #         task,
    #         default_ext,
    #         timeout,
    #         max_retry,
    #         min_size=min_size,
    #         max_size=max_size)
