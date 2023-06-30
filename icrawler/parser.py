import logging
import queue
import time
from threading import current_thread
from urllib.parse import urlsplit

from icrawler.utils import ThreadPool


class Parser(ThreadPool):
    """Base class for parser.

    A thread pool of parser threads, in charge of downloading and parsing pages,
    extracting file urls and put them into the input queue of downloader.

    Attributes:
        global_signal: A Signal object for cross-module communication.
        session: A requests.Session object.
        logger: A logging.Logger object used for logging.
        threads: A list storing all the threading.Thread objects of the parser.
        thread_num: An integer indicating the number of threads.
        lock: A threading.Lock object.
    """

    def __init__(self, thread_num, signal, session):
        """Init Parser with some shared variables."""
        super().__init__(thread_num, name="parser")
        self.signal = signal
        self.session = session

    def parse(self, response, **kwargs):
        """Parse a page and extract image urls, then put it into task_queue.

        This method should be overridden by users.

        :Example:

        >>> task = {}
        >>> self.output(task)
        """
        raise NotImplementedError

    def worker_exec(self, queue_timeout=2, req_timeout=5, max_retry=3, **kwargs):
        """Target method of workers.

        Firstly download the page and then call the :func:`parse` method.
        A parser thread will exit in either of the following cases:

        1. All feeder threads have exited and the ``url_queue`` is empty.
        2. Downloaded image number has reached required number.

        Args:
            queue_timeout (int): Timeout of getting urls from ``url_queue``.
            req_timeout (int): Timeout of making requests for downloading pages.
            max_retry (int): Max retry times if the request fails.
            **kwargs: Arguments to be passed to the :func:`parse` method.
        """
        while True:
            if self.signal.get("reach_max_num"):
                self.logger.info(
                    "downloaded image reached max num, thread %s " "is ready to exit", current_thread().name
                )
                break
            # get the page url
            try:
                url = self.in_queue.get(timeout=queue_timeout)
            except queue.Empty:
                if self.signal.get("feeder_exited"):
                    self.logger.info("no more page urls for thread %s to parse", current_thread().name)
                    break
                else:
                    self.logger.info("%s is waiting for new page urls", current_thread().name)
                    continue
            except:
                self.logger.error("exception in thread %s", current_thread().name)
                continue
            else:
                self.logger.debug(f"start fetching page {url}")
            # fetch and parse the page
            retry = max_retry
            while retry > 0:
                try:
                    base_url = "{0.scheme}://{0.netloc}".format(urlsplit(url))
                    response = self.session.get(url, timeout=req_timeout, headers={"Referer": base_url})
                except Exception as e:
                    self.logger.error(
                        "Exception caught when fetching page %s, " "error: %s, remaining retry times: %d",
                        url,
                        e,
                        retry - 1,
                    )
                else:
                    self.logger.info(f"parsing result page {url}")
                    for task in self.parse(response, **kwargs):
                        while not self.signal.get("reach_max_num"):
                            try:
                                if isinstance(task, dict):
                                    self.output(task, timeout=1)
                                elif isinstance(task, str):
                                    # this case only work for GreedyCrawler,
                                    # which need to feed the url back to
                                    # url_queue, dirty implementation
                                    self.input(task, timeout=1)
                            except queue.Full:
                                time.sleep(1)
                            except Exception as e:
                                self.logger.error(
                                    "Exception caught when put task %s into " "queue, error: %s", task, url
                                )
                            else:
                                break
                        if self.signal.get("reach_max_num"):
                            break
                    self.in_queue.task_done()
                    break
                finally:
                    retry -= 1
        self.logger.info(f"thread {current_thread().name} exit")

    def __exit__(self):
        logging.info("all parser threads exited")
