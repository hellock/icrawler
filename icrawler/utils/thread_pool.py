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

    def __init__(self, thread_num, in_queue=None, out_queue=None, name=None):
        self.thread_num = thread_num
        self.in_queue = (in_queue
                         if in_queue else CachedQueue(5 * self.thread_num))
        self.out_queue = (out_queue
                          if out_queue else CachedQueue(5 * self.thread_num))
        self.name = name if name else __name__
        self._workers = []
        self.lock = Lock()
        self.logger = logging.getLogger(self.name)

    def init_workers(self, *args, **kwargs):
        for i in range(self.thread_num):
            worker = Worker(
                target=self.worker_exec,
                name='{}-{:03d}'.format(self.name, i + 1),
                args=args,
                kwargs=kwargs)
            self._workers.append(worker)

    def start(self, *args, **kwargs):
        self.init_workers(*args, **kwargs)
        for worker in self._workers:
            self.logger.debug('thread %s started', worker.name)
            worker.start()

    def input(self, task, block=True, timeout=None):
        if self.in_queue is not None:
            self.in_queue.put(task, block, timeout)

    def output(self, task, block=True, timeout=None):
        if self.out_queue is not None:
            self.out_queue.put(task, block, timeout)

    def worker_exec(self, *args, **kwargs):
        raise NotImplementedError

    def connect(self, component):
        if not isinstance(component, ThreadPool):
            raise TypeError('"component" must be a ThreadPool object')
        component.in_queue = self.out_queue
        return component

    def is_alive(self):
        for worker in self._workers:
            if worker.is_alive():
                return True
        return False

    def terminate(self):
        for worker in self._workers:
            worker.terminate()
