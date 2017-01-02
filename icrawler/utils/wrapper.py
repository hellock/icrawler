import json
from collections import OrderedDict
from threading import Thread

from six.moves.queue import Queue


class DaemonThread(Thread):
    """A wrapper for daemon thread

    Since Thread class in Python 2.x does not support the `daemon` argument when
    initialing, this wrapper just add `daemon=True` by default.
    """

    def __init__(self, *args, **kwargs):
        super(DaemonThread, self).__init__(*args, **kwargs)
        self.daemon = True


class CachedQueue(Queue):
    """Queue with cache"""

    def __init__(self, cache_capacity=0, *args, **kwargs):
        super(CachedQueue, self).__init__(*args, **kwargs)
        self.cache_capacity = cache_capacity
        self._cache = OrderedDict()

    def check_dup(self, item):
        """Check whether the item has been in the cache

        If the item has not been seen before, then hash it and put it into
        the cache, otherwise indicates the item is duplicated. When the cache
        size exceeds capacity, discard the earliest items in the cache.
        """
        if isinstance(item, dict):
            hashable_item = json.dumps(item, sort_keys=True)
        elif isinstance(item, list):
            hashable_item = frozenset(item)
        else:
            hashable_item = item
        if hashable_item in self._cache:
            return True
        else:
            if self.cache_capacity > 0 and len(self._cache) >= self.cache_capacity:
                self._cache.popitem(False)
            self._cache[hashable_item] = 1
            return False

    def put(self, item, dup_callback=None):
        if self.check_dup(item):
            super(CachedQueue, self).put(item)
        else:
            if dup_callback:
                dup_callback(item)
