import logging
from threading import Lock, Thread

from .cached_queue import CachedQueue


class Worker(Thread):

    def __init__(self, *args, **kwargs):
        super(Worker, self).__init__(*args, **kwargs)
        self.daemon = True
        self.quit = False

    def terminate(self):
        self.quit = True


class ThreadPool(object):
    """Simple implementation of a thread pool

    This is the base class of :class:`Feeder`, :class:`Parser` and
    :class:`Downloader`, it incorporates two FIFO queues and a number of
    "workers", namely threads. All threads share the two queues, after each
    thread starts, it will watch the ``in_queue``, once the queue is not empty,
    it will get a task from the queue and process as wanted, then it will put
    the output to ``out_queue``.

    Note:
        This class is not designed as a generic thread pool, but works
        specifically for crawler components.

    Attributes:
        name (str): thread pool name.
        thread_num (int): number of available threads.
        in_queue (Queue): input queue of tasks.
        out_queue (Queue): output queue of finished tasks.
        workers (list): a list of working threads.
        lock (Lock): thread lock.
        logger (Logger): standard python logger.
    """

    def __init__(self, thread_num, in_queue=None, out_queue=None, name=None):
        self.thread_num = thread_num
        self.in_queue = (in_queue
                         if in_queue else CachedQueue(5 * self.thread_num))
        self.out_queue = (out_queue
                          if out_queue else CachedQueue(5 * self.thread_num))
        self.name = name if name else __name__
        self.workers = []
        self.lock = Lock()
        self.logger = logging.getLogger(self.name)

    def init_workers(self, *args, **kwargs):
        self.workers = []
        for i in range(self.thread_num):
            worker = Worker(
                target=self.worker_exec,
                name='{}-{:03d}'.format(self.name, i + 1),
                args=args,
                kwargs=kwargs)
            self.workers.append(worker)

    def start(self, *args, **kwargs):
        self.init_workers(*args, **kwargs)
        for worker in self.workers:
            self.logger.debug('thread %s started', worker.name)
            worker.start()

    def input(self, task, block=True, timeout=None):
        if self.in_queue is not None:
            self.in_queue.put(task, block, timeout)

    def output(self, task, block=True, timeout=None):
        if self.out_queue is not None:
            self.out_queue.put(task, block, timeout)

    def clear_buffer(self, clear_out=False):
        self.in_queue.queue.clear()
        if clear_out:
            self.out_queue.queue.clear()

    def worker_exec(self, *args, **kwargs):
        raise NotImplementedError

    def connect(self, component):
        """Connect two ThreadPools.

        The ``in_queue`` of the second pool will be set as the ``out_queue`` of
        the current pool, thus all the output will be input to the second pool.

        Args:
            component (ThreadPool): the ThreadPool to be connected.
        Returns:
            ThreadPool: the modified second ThreadPool.
        """
        if not isinstance(component, ThreadPool):
            raise TypeError('"component" must be a ThreadPool object')
        component.in_queue = self.out_queue
        return component

    def is_alive(self):
        for worker in self.workers:
            if worker.is_alive():
                return True
        return False

    def terminate(self):
        for worker in self.workers:
            worker.terminate()
