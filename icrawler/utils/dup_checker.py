# -*- coding: utf-8 -*-

import json
from collections import OrderedDict


class DupChecker(object):
    """A checker to filter out duplicated urls or tasks.

    Use an OrderedDict to store most recent urls or tasks, each time when
    a new item comes, check weather it is already in the dict.

    Attributes:
        cache_size: An interger that controls the capacity of cache
                    (default 0, meaning unlimited capacity)
        cache_dict: A dict storing all the recent items
    """

    def __init__(self, capacity=0):
        """Init the DupChecker with specified cache capacity."""
        self.capacity = capacity
        self._cache = OrderedDict()

    def check(self, item):
        """Check whether the item has been in the cache

        If the item has not been seen before, then hash it and put it into
        the cache, otherwise indicates the item is duplicated. When the cache
        size exceeds capacity, discard the earliest items in the cache.

        Args:
            item: A dict or list or string to be checked.

        Returns:
            A boolean indicating if the item has been seen recently.
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
            if self.capacity > 0 and len(self._cache) >= self.capacity:
                self._cache.popitem(False)
            self._cache[hashable_item] = 1
            return False
