import json
from collections import OrderedDict

from six.moves.queue import Queue


class CachedQueue(Queue, object):
    """Queue with cache

    This queue is used in :class:`ThreadPool`, it enables parser and downloader
    to check if the page url or the task has been seen or processed before.

    Attributes:
        _cache (OrderedDict): cache, elements are stored as keys of it.
        cache_capacity (int): maximum size of cache.

    """

    def __init__(self, *args, **kwargs):
        super(CachedQueue, self).__init__(*args, **kwargs)
        if 'cache_capacity' in kwargs:
            self.cache_capacity = kwargs['cache_capacity']
        else:
            self.cache_capacity = 0
        self._cache = OrderedDict()

    def is_duplicated(self, item):
        """Check whether the item has been in the cache

        If the item has not been seen before, then hash it and put it into
        the cache, otherwise indicates the item is duplicated. When the cache
        size exceeds capacity, discard the earliest items in the cache.

        Args:
            item (object): The item to be checked and stored in cache. It must
                be immutable or a list/dict.
        Returns:
            bool: Whether the item has been in cache.
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
            if self.cache_capacity > 0 and len(
                    self._cache) >= self.cache_capacity:
                self._cache.popitem(False)
            self._cache[hashable_item] = 1
            return False

    def put(self, item, block=True, timeout=None, dup_callback=None):
        """Put an item to queue if it is not duplicated.
        """
        if not self.is_duplicated(item):
            super(CachedQueue, self).put(item, block, timeout)
        else:
            if dup_callback:
                dup_callback(item)

    def put_nowait(self, item, dup_callback=None):
        self.put(item, block=False, dup_callback=dup_callback)
